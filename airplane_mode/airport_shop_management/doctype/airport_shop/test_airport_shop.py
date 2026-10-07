# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from airplane_mode.airport_shop_management.doctype.airport_shop.airport_shop import get_shop_statistics


class TestAirportShop(FrappeTestCase):
	def setUp(self):
		# Clean up any test shops
		frappe.db.delete("Airport Shop", {"shop_number": ["in", ["T-101", "T-102", "T-103"]]})
		self.ensure_test_airports()

	def ensure_test_airports(self):
		if not frappe.db.exists("Airport", "Test Airport Alpha"):
			frappe.get_doc({
				"doctype": "Airport",
				"name": "Test Airport Alpha",
				"code": "ALPHA",
				"city": "Alpha City",
				"country": "India"
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Airport", "Test Airport Beta"):
			frappe.get_doc({
				"doctype": "Airport",
				"name": "Test Airport Beta",
				"code": "BETA",
				"city": "Beta City",
				"country": "India"
			}).insert(ignore_permissions=True)

	def test_shop_number_uniqueness_per_airport(self):
		# Shop T-101 in Alpha: valid
		shop1 = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-101",
			"shop_name": "Alpha Shop 101",
			"airport": "Test Airport Alpha",
			"area": 250,
			"rent_amount": 30000,
			"shop_status": "Available"
		}).insert()
		self.assertTrue(shop1.name)

		# Same shop number in different airport (Beta): valid
		shop2 = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-101",
			"shop_name": "Beta Shop 101",
			"airport": "Test Airport Beta",
			"area": 300,
			"rent_amount": 35000,
			"shop_status": "Available"
		}).insert()
		self.assertTrue(shop2.name)

		# Duplicate shop number in same airport (Alpha): invalid
		dup_shop = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-101",
			"shop_name": "Duplicate Alpha 101",
			"airport": "Test Airport Alpha",
			"area": 250,
			"rent_amount": 30000,
			"shop_status": "Available"
		})
		self.assertRaises(frappe.ValidationError, dup_shop.insert)

	def test_area_validation(self):
		shop = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-102",
			"shop_name": "Zero Area Shop",
			"airport": "Test Airport Alpha",
			"area": 0,
			"rent_amount": 30000,
			"shop_status": "Available"
		})
		self.assertRaises(frappe.ValidationError, shop.insert)

		shop.area = -50
		self.assertRaises(frappe.ValidationError, shop.insert)

	def test_occupied_without_contract_rejected(self):
		shop = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-103",
			"shop_name": "Premature Occupied",
			"airport": "Test Airport Alpha",
			"area": 200,
			"rent_amount": 25000,
			"shop_status": "Occupied"
		})
		self.assertRaises(frappe.ValidationError, shop.insert)

	def test_shop_statistics(self):
		stats = get_shop_statistics("Test Airport Alpha")
		self.assertIn("total", stats)
		self.assertIn("available", stats)
		self.assertIn("occupied", stats)
		self.assertIn("under_maintenance", stats)

	def test_shop_type_validation(self):
		if not frappe.db.exists("Shop Type", "Stall"):
			frappe.get_doc({"doctype": "Shop Type", "shop_type": "Stall", "enabled": 1}).insert(ignore_permissions=True)
		if not frappe.db.exists("Shop Type", "Disabled Type"):
			frappe.get_doc({"doctype": "Shop Type", "shop_type": "Disabled Type", "enabled": 0}).insert(ignore_permissions=True)

		# Valid enabled type
		shop_ok = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-104",
			"shop_name": "Stall Shop",
			"airport": "Test Airport Alpha",
			"shop_type": "Stall",
			"area": 100,
			"rent_amount": 15000,
			"shop_status": "Available"
		}).insert()
		self.assertEqual(shop_ok.shop_type, "Stall")

		# Disabled type rejected
		shop_bad = frappe.get_doc({
			"doctype": "Airport Shop",
			"shop_number": "T-105",
			"shop_name": "Disabled Type Shop",
			"airport": "Test Airport Alpha",
			"shop_type": "Disabled Type",
			"area": 100,
			"rent_amount": 15000,
			"shop_status": "Available"
		})
		self.assertRaises(frappe.ValidationError, shop_bad.insert)
