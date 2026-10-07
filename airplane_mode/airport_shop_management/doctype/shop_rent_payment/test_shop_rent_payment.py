# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days
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

		# Create a contract: 2026-06-01 to 2026-12-31
		self.contract = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TPA-901",
			"tenant": "Test Payment Tenant",
			"contract_start_date": "2026-06-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": 30000,
			"contract_status": "Draft"  # Don't auto-schedule to test manual payment
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
		# Contract is 2026-06 to 2026-12
		p = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-03"
		})
		self.assertRaises(frappe.ValidationError, p.insert)

	def test_tampering_rejection_and_derived_fetch(self):
		# Create payment with tampered shop
		tampered = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-07",
			"shop": "TAMPERED-SHOP"
		})
		self.assertRaises(frappe.ValidationError, tampered.insert)

		# Valid payment: correctly fetches shop, tenant, airport, amount_due
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

	def test_amounts_and_status_transitions(self):
		# Overpayment rejection
		p_over = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09",
			"amount_paid": 35000,
			"payment_date": today()
		})
		self.assertRaises(frappe.ValidationError, p_over.insert)

		# Paid without payment date rejection
		p_no_date = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09",
			"amount_paid": 30000
		})
		self.assertRaises(frappe.ValidationError, p_no_date.insert)

		# Future payment date rejection
		p_future = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09",
			"amount_paid": 30000,
			"payment_date": add_days(today(), 5)
		})
		self.assertRaises(frappe.ValidationError, p_future.insert)

		# Partially paid calculation
		p_partial = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-09",
			"amount_paid": 15000,
			"payment_date": today()
		}).insert()
		self.assertEqual(p_partial.payment_status, "Partially Paid")

		# Fully paid calculation
		p_paid = frappe.get_doc({
			"doctype": "Shop Rent Payment",
			"contract": self.contract.name,
			"rent_month": "2026-10",
			"amount_paid": 30000,
			"payment_date": today()
		}).insert()
		self.assertEqual(p_paid.payment_status, "Paid")

	def test_rent_reminder_scheduler(self):
		settings = frappe.get_single("Shop Management Settings")
		settings.enable_rent_reminders = 0
		settings.save()

		# When disabled, returns 0
		sent = send_rent_reminders()
		self.assertEqual(sent, 0)
