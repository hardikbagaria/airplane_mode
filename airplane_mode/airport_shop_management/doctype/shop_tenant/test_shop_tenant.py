# Copyright (c) 2026, Haradik Bagaria - AESPL and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestShopTenant(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Shop Tenant", {"tenant_name": ["in", ["Test Tenant A", "Test Tenant B"]]})

	def test_tenant_validations(self):
		# Valid tenant
		tenant = frappe.get_doc({
			"doctype": "Shop Tenant",
			"tenant_name": "Test Tenant A",
			"company_name": "Acme Retail Ltd",
			"email": "retail@acme.com",
			"phone": "+919876543210",
			"gstin": "27AABCU9603R1ZM",
			"status": "Active"
		})
		tenant.insert()
		self.assertTrue(tenant.name)

		# Invalid email
		invalid_email = frappe.get_doc({
			"doctype": "Shop Tenant",
			"tenant_name": "Test Tenant B",
			"company_name": "Bad Email Ltd",
			"email": "not-an-email",
			"phone": "9876543210"
		})
		self.assertRaises(frappe.ValidationError, invalid_email.insert)

		# Invalid phone
		invalid_phone = frappe.get_doc({
			"doctype": "Shop Tenant",
			"tenant_name": "Test Tenant B",
			"company_name": "Bad Phone Ltd",
			"email": "valid@email.com",
			"phone": "abc"
		})
		self.assertRaises(frappe.ValidationError, invalid_phone.insert)

		# Invalid GSTIN
		invalid_gstin = frappe.get_doc({
			"doctype": "Shop Tenant",
			"tenant_name": "Test Tenant B",
			"company_name": "Bad GSTIN Ltd",
			"email": "valid@email.com",
			"phone": "9876543210",
			"gstin": "INVALID123"
		})
		self.assertRaises(frappe.ValidationError, invalid_gstin.insert)
