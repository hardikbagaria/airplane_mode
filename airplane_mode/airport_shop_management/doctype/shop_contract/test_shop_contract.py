# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract import (
	generate_due_rent_receipts,
	generate_rent_receipt_for_month,
	renew_contract,
	terminate_contract,
)


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
		})
		self.assertRaises(frappe.ValidationError, c.insert)

	def test_contract_submit_and_overlap_prevention(self):
		# Contract A: 2026-01-01 to 2026-12-31
		contract_a = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-01-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": 40000,
		}).insert()
		self.assertEqual(contract_a.docstatus, 0)
		self.assertEqual(contract_a.contract_status, "Draft")

		# Submit contract A
		contract_a.submit()
		self.assertEqual(contract_a.docstatus, 1)
		self.assertEqual(contract_a.contract_status, "Active")

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
		}).insert()
		# When submitted, should raise overlap validation error
		self.assertRaises(frappe.ValidationError, contract_b.submit)

	def test_contract_cancel_and_shop_release(self):
		contract = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-01-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": 40000,
		}).insert()
		contract.submit()

		# Shop is Occupied
		self.assertEqual(frappe.db.get_value("Airport Shop", "TCA-501", "shop_status"), "Occupied")

		# Cancel contract
		contract.cancel()
		self.assertEqual(contract.docstatus, 2)
		self.assertEqual(contract.contract_status, "Cancelled")

		# Shop should revert to Available
		self.assertEqual(frappe.db.get_value("Airport Shop", "TCA-501", "shop_status"), "Available")
		self.assertIsNone(frappe.db.get_value("Airport Shop", "TCA-501", "current_contract"))

	def test_actions_terminate_and_renew(self):
		contract = frappe.get_doc({
			"doctype": "Shop Contract",
			"shop": "TCA-501",
			"tenant": "Test Contract Tenant 1",
			"contract_start_date": "2026-01-01",
			"contract_end_date": "2026-12-31",
			"monthly_rent": 40000,
		}).insert()
		contract.submit()

		# Terminate action
		terminate_contract(contract.name)
		contract.reload()
		self.assertEqual(contract.contract_status, "Terminated")
		self.assertEqual(frappe.db.get_value("Airport Shop", "TCA-501", "shop_status"), "Available")

		# Renew action
		renewed_name = renew_contract(contract.name)
		renewed = frappe.get_doc("Shop Contract", renewed_name)
		self.assertEqual(str(renewed.contract_start_date), "2027-01-01")
		self.assertEqual(renewed.docstatus, 0)
