# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestShopLead(FrappeTestCase):
	def setUp(self):
		self.ensure_test_shops()

	def ensure_test_shops(self):
		if not frappe.db.exists("Airport", "Test Lead Airport"):
			frappe.get_doc({
				"doctype": "Airport",
				"name": "Test Lead Airport",
				"code": "TLA",
				"city": "Lead City",
				"country": "India"
			}).insert(ignore_permissions=True)

		# Available shop
		if not frappe.db.exists("Airport Shop", "TLA-101"):
			frappe.get_doc({
				"doctype": "Airport Shop",
				"shop_number": "101",
				"shop_name": "Available Shop 101",
				"airport": "Test Lead Airport",
				"area": 200,
				"rent_amount": 20000,
				"shop_status": "Available"
			}).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Airport Shop", "TLA-101", "shop_status", "Available")

		# Maintenance shop
		if not frappe.db.exists("Airport Shop", "TLA-102"):
			frappe.get_doc({
				"doctype": "Airport Shop",
				"shop_number": "102",
				"shop_name": "Maint Shop 102",
				"airport": "Test Lead Airport",
				"area": 200,
				"rent_amount": 20000,
				"shop_status": "Under Maintenance"
			}).insert(ignore_permissions=True)
		else:
			frappe.db.set_value("Airport Shop", "TLA-102", "shop_status", "Under Maintenance")

		frappe.db.delete("Shop Lead", {"email": ["in", ["lead@test.com", "bad@test.com"]]})

	def test_lead_validations(self):
		# Missing name
		l_no_name = frappe.get_doc({
			"doctype": "Shop Lead",
			"shop": "TLA-101",
			"name1": "",
			"email": "lead@test.com"
		})
		self.assertRaises(frappe.ValidationError, l_no_name.insert)

		# Invalid email
		l_bad_email = frappe.get_doc({
			"doctype": "Shop Lead",
			"shop": "TLA-101",
			"name1": "John Doe",
			"email": "not-an-email"
		})
		self.assertRaises(frappe.ValidationError, l_bad_email.insert)

		# Non-existent shop
		l_no_shop = frappe.get_doc({
			"doctype": "Shop Lead",
			"shop": "NON-EXISTENT-SHOP",
			"name1": "John Doe",
			"email": "lead@test.com"
		})
		self.assertRaises(frappe.ValidationError, l_no_shop.insert)

		# Shop under maintenance (not available for lease)
		l_maint = frappe.get_doc({
			"doctype": "Shop Lead",
			"shop": "TLA-102",
			"name1": "John Doe",
			"email": "lead@test.com"
		})
		self.assertRaises(frappe.ValidationError, l_maint.insert)

		# Valid lead on Available shop
		valid_lead = frappe.get_doc({
			"doctype": "Shop Lead",
			"shop": "TLA-101",
			"name1": "John Doe",
			"email": "lead@test.com",
			"phone": "+919876543210",
			"company_name": "Doe Retailers",
			"message": "Interested in opening a coffee shop."
		}).insert()
		self.assertTrue(valid_lead.name)
		self.assertEqual(valid_lead.status, "New")
		self.assertEqual(valid_lead.airport, "Test Lead Airport")
		self.assertEqual(valid_lead.shop_number, "101")
