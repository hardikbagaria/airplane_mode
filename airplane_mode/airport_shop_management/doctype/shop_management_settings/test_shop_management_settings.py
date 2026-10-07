# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestShopManagementSettings(FrappeTestCase):
	def test_default_rent_amount_validation(self):
		settings = frappe.get_single("Shop Management Settings")
		settings.default_rent_amount = -100
		self.assertRaises(frappe.ValidationError, settings.save)

		settings.default_rent_amount = 0
		self.assertRaises(frappe.ValidationError, settings.save)

		settings = frappe.get_doc("Shop Management Settings")
		settings.default_rent_amount = 50000
		settings.enable_rent_reminders = 1
		settings.save()
		self.assertEqual(settings.default_rent_amount, 50000)
