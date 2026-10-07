# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import validate_email_address


class ShopTenant(Document):
	def validate(self):
		self.validate_tenant_name()
		self.validate_email()
		self.validate_phone()
		self.validate_gstin()
		self.validate_status()

	def validate_tenant_name(self):
		if not self.tenant_name or not self.tenant_name.strip():
			frappe.throw(_("Tenant Name is required."))

	def validate_email(self):
		if self.email:
			self.email = self.email.strip()
			validate_email_address(self.email, throw=True)

	def validate_phone(self):
		if self.phone:
			# Strip out common separators
			clean_phone = re.sub(r"[\s\-\(\)\+]", "", self.phone.strip())
			if not clean_phone.isdigit() or len(clean_phone) < 7 or len(clean_phone) > 15:
				frappe.throw(_("Please enter a valid phone number (7 to 15 digits)."))

	def validate_gstin(self):
		if self.gstin:
			# Indian GSTIN: 15 alphanumeric characters
			# 2 digits state code, 10 characters PAN, 1 entity number, 'Z', 1 checksum char
			gstin_clean = self.gstin.strip().upper()
			gstin_pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
			if not re.match(gstin_pattern, gstin_clean):
				frappe.throw(
					_("Invalid GSTIN format. Expected 15-character alphanumeric format (e.g. 22AAAAA0000A1Z5).")
				)
			self.gstin = gstin_clean

	def validate_status(self):
		valid_statuses = ["Active", "Inactive"]
		if self.status and self.status not in valid_statuses:
			frappe.throw(_("Status must be one of: {0}.").format(", ".join(valid_statuses)))
