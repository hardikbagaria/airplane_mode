# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ShopManagementSettings(Document):
	def validate(self):
		if self.default_rent_amount is not None and flt(self.default_rent_amount) <= 0:
			frappe.throw(_("Default Rent Amount must be greater than 0."))
