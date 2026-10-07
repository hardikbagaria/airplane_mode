# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract import generate_rent_schedule


class TestShopContract(FrappeTestCase):
	def setUp(self):
		self.ensure_test_data()

	def ensure_test_data(self):
		if not frappe.db.exists("Airport", "Test Contract Airport"):
			frappe.get_doc({
				"doctype": "Airport",
				"name": "Test Contract Airport",
				"code": "TCA",
				"city": "Contract City",
				"country": "India"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Shop Tenant", "Test Contract Tenant 1"):
			frappe.get_doc({
				"doctype": "Shop Tenant",
				"tenant_name": "Test Contract Tenant 1",
				"company_name": "Contract Tenant 1 Corp",
				"email": "tenant1@contract.com",
				"status": "Active"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Shop Tenant", "Test Contract Tenant 2"):
			frappe.get_doc({
				"doctype": "Shop Tenant",
				"tenant_name": "Test Contract Tenant 2",
				"company_name": "Contract Tenant 2 Corp",
				"email": "tenant2@contract.com",
				"status": "Active"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Airport Shop", "TCA-501"):
			frappe.get_doc({
				"doctype": "Airport Shop",
				"shop_number": "501",
				"shop_name": "Contract Shop 501",
				"airport": "Test Contract Airport",
				"area": 200,
				"rent_amount": 40000,
				"shop_status": "Available"
			}).insert(ignore_permissions=True)

		# Delete any existing contracts on this shop
		frappe.db.delete("Shop Rent Payment", {"shop": "TCA-501"})
		frappe.db.delete("Shop Contract", {"shop": "TCA-501"})
		frappe.db.set_value("Airport Shop", "TCA-501", {
			"shop_status": "Available",
			"current_contract": None,
			"current_tenant": None
		})

	def test_contract_date_validations(self):
		# End before start
		c1 = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-12-31",
			"contract_end_date": "2026-01-01",
			"monthly_rent": 40000,
			"contract_status": "Active"
		})
		self.assertRaises(frappe.ValidationError, c1.insert)

		# Same start and end date
		c2 = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-05-01",
			"contract_end_date": "2026-05-01",
			"monthly_rent": 40000,
			"contract_status": "Active"
		})
		self.assertRaises(frappe.ValidationError, c2.insert)

	def test_monthly_rent_validation(self):
		c = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-01-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": -500,
			"contract_status": "Active"
		})
		self.assertRaises(frappe.ValidationError, c.insert)

	def test_contract_overlap_prevention(self):
		# Contract A: 2026-01-01 to 2026-12-31
		contract_a = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-01-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": 40000,
			"contract_status": "Active"
		}).insert()
		self.assertTrue(contract_a.name)

		# Verify shop is Occupied
		shop = frappe.get_doc("Airport Shop", "TCA-501")
		self.assertEqual(shop.shop_status, "Occupied")
		self.assertEqual(shop.current_contract, contract_a.name)

		# Contract B: 2026-10-01 to 2027-09-30 (Overlaps!)
		contract_b = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 2",
			"contract_start_date": "2026-10-01",
			"contract_end_date": "2027-09-30",
			"monthly_rent": 42000,
			"contract_status": "Active"
		})
		self.assertRaises(frappe.ValidationError, contract_b.insert)

	def test_schedule_generation_and_idempotence(self):
		# Create contract for 3 months
		contract = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-01-01",
			"contract_end_date": "2026-03-31",
			"monthly_rent": 40000,
			"contract_status": "Active"
		}).insert()

		payments = frappe.get_all(
			"Shop Rent Payment",
			filters={"contract": contract.name},
			fields=["name", "rent_month", "amount_due", "payment_status"]
		)
		# Should have 3 payments: 2026-01, 2026-02, 2026-03
		self.assertEqual(len(payments), 3)

		# Run schedule generation again: must be idempotent and not create duplicates
		new_payments = generate_rent_schedule(contract.name)
		self.assertEqual(len(new_payments), 0)

		payments_after = frappe.get_all(
			"Shop Rent Payment",
			filters={"contract": contract.name}
		)
		self.assertEqual(len(payments_after), 3)
