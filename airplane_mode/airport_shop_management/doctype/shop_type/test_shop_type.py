# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from airplane_mode.airport_shop_management.doctype.shop_type.shop_type import create_default_shop_types


class TestShopType(FrappeTestCase):
	def test_default_shop_types_created(self):
		create_default_shop_types()
		for expected in ["Stall", "Walk-through", "Normal"]:
			self.assertTrue(frappe.db.exists("Shop Type", expected))
			enabled = frappe.db.get_value("Shop Type", expected, "enabled")
			self.assertEqual(enabled, 1)

	def test_shop_type_validation(self):
		# Cannot create empty shop type
		empty_type = frappe.get_doc({
			"doctype": "Shop Type",
			"shop_type": "",
			"enabled": 1
		})
		self.assertRaises(frappe.ValidationError, empty_type.insert)
