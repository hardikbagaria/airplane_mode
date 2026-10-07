# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, validate_email_address


class ShopLead(Document):
	def before_insert(self):
		if not self.created_on:
			self.created_on = now_datetime()
		if not self.status:
			self.status = "New"

	def validate(self):
		self.validate_applicant_info()
		self.validate_shop_availability()

	def validate_applicant_info(self):
		if not self.name1 or not self.name1.strip():
			frappe.throw(_("Name is required."))

		if not self.email or not self.email.strip():
			frappe.throw(_("Email is required."))

		self.email = self.email.strip()
		validate_email_address(self.email, throw=True)

		if self.phone:
			clean_phone = re.sub(r"[\s\-\(\)\+]", "", self.phone.strip())
			if not clean_phone.isdigit() or len(clean_phone) < 7 or len(clean_phone) > 15:
				frappe.throw(_("Please enter a valid phone number (7 to 15 digits)."))

	def validate_shop_availability(self):
		if not self.shop:
			frappe.throw(_("Shop is required."))

		shop = frappe.db.get_value(
			"Airport Shop",
			self.shop,
			["name", "shop_status", "airport", "shop_number", "shop_name"],
			as_dict=True,
		)
		if not shop:
			frappe.throw(_("Selected Shop does not exist."))

		if shop.shop_status != "Available":
			frappe.throw(_("The selected shop is not currently available for lease."))

		self.airport = shop.airport
		self.shop_number = shop.shop_number
		self.shop_name = shop.shop_name

		valid_statuses = ["New", "Contacted", "Converted", "Rejected"]
		if self.status and self.status not in valid_statuses:
			frappe.throw(_("Status must be one of: {0}.").format(", ".join(valid_statuses)))
