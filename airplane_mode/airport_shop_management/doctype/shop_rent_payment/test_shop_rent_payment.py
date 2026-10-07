# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days
from airplane_mode.airport_shop_management.doctype.shop_rent_payment.shop_rent_payment import (
	mark_as_paid_and_submit,
)
from airplane_mode.airport_shop_management.tasks import send_rent_reminders


class TestShopRentPayment(FrappeTestCase):
	def setUp(self):
		self.ensure_test_contract()

	def ensure_test_contract(self):
		if not frappe.db.exists("Airport", "Test Payment Airport"):
			frappe.get_doc({
				"doctype": "Airport",
				"name": "Test Payment Airport",
				"code": "TPA",
				"city": "Pay City",
				"country": "India"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Shop Tenant", "Test Payment Tenant"):
			frappe.get_doc({
				"doctype": "Shop Tenant",
				"tenant_name": "Test Payment Tenant",
				"company_name": "Payment Tenant Corp",
				"email": "paytenant@test.com",
				"status": "Active"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Airport Shop", "TPA-901"):
			frappe.get_doc({
				"doctype": "Airport Shop",
				"shop_number": "901",
				"shop_name": "Pay Shop 901",
				"airport": "Test Payment Airport",
				"area": 180,
				"rent_amount": 30000,
				"shop_status": "Available"
			}).insert(ignore_permissions=True)

		# Clear existing
		frappe.db.delete("Shop Rent Payment", {"shop": "TPA-901"})
		frappe.db.delete("Shop Contract", {"shop": "TPA-901"})
		frappe.db.set_value("Airport Shop", "TPA-901", {
			"shop_status": "Available",
			"current_contract": None,
			"current_tenant": None
		})

		# Create a contract: 2026-06-01 to 2026-12-31 in Draft
		self.contract = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TPA-901",
			"tenant": "Test Payment Tenant",
			"contract_start_date": "2026-06-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": 30000,
			"contract_status": "Draft"
		}).insert()

	def test_rent_month_format_validation(self):
		invalid_months = ["10/2026", "October 2026", "2026/10", "2026-1", "2026-13", "2026-00"]
		for m in invalid_months:
			p = frappe.get_doc({
				"doctype": "Shop Rent Payment",
				"contract": self.contract.name,
				"rent_month": m
			})
			self.assertRaises(frappe.ValidationError, p.insert)

	def test_month_outside_contract_duration(self):
		p = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-03"
		})
		self.assertRaises(frappe.ValidationError, p.insert)

	def test_due_date_calculation_10th(self):
		# Rent for 2026-09 is due on 2026-10-10
		p = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09"
		}).insert()
		self.assertEqual(p.due_date, "2026-10-10")

		# Rent for 2026-07 is due on 2026-08-10
		p7 = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-07"
		}).insert()
		self.assertEqual(p7.due_date, "2026-08-10")

	def test_tampering_rejection_and_derived_fetch(self):
		tampered = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-07",
			"shop": "TAMPERED-SHOP"
		})
		self.assertRaises(frappe.ValidationError, tampered.insert)

		valid_p = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-07"
		}).insert()
		self.assertEqual(valid_p.shop, "TPA-901")
		self.assertEqual(valid_p.tenant, "Test Payment Tenant")
		self.assertEqual(valid_p.airport, "Test Payment Airport")
		self.assertEqual(valid_p.amount_due, 30000)

	def test_duplicate_contract_month_prevention(self):
		p1 = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-08"
		}).insert()
		self.assertTrue(p1.name)

		p2 = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-08"
		})
		self.assertRaises(frappe.ValidationError, p2.insert)

	def test_amounts_and_submission(self):
		# Overpayment rejection
		p_over = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09",
			"amount_paid": 35000,
			"payment_date": today()
		})
		self.assertRaises(frappe.ValidationError, p_over.insert)

		# Cannot submit with 0 payment
		p_zero = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09",
			"amount_paid": 0
		}).insert()
		self.assertRaises(frappe.ValidationError, p_zero.submit)

		# Submit with full payment
		p_zero.amount_paid = 30000
		p_zero.payment_date = today()
		p_zero.submit()
		self.assertEqual(p_zero.docstatus, 1)
		self.assertEqual(p_zero.payment_status, "Paid")

	def test_action_mark_as_paid_and_submit(self):
		p = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-11",
			"amount_paid": 0
		}).insert()
		self.assertEqual(p.docstatus, 0)

		# Action button helper
		mark_as_paid_and_submit(p.name, payment_mode="UPI", transaction_reference="UPI-REF-123")
		p.reload()
		self.assertEqual(p.docstatus, 1)
		self.assertEqual(p.payment_status, "Paid")
		self.assertEqual(p.payment_mode, "UPI")
		self.assertEqual(p.transaction_reference, "UPI-REF-123")

	def test_rent_reminder_scheduler(self):
		settings = frappe.get_single("Shop Management Settings")
		settings.enable_rent_reminders = 0
		settings.save()

		sent = send_rent_reminders()
		self.assertEqual(sent, 0)
