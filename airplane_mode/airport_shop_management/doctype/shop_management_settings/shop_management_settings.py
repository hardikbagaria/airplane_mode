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


@frappe.whitelist()
def trigger_generate_all_due_receipts():
	"""
	Action button method: runs batch generation of due rent receipts across all active contracts.
	"""
	from airplane_mode.airport_shop_management.tasks import generate_due_monthly_rent_receipts
	count = generate_due_monthly_rent_receipts()
	return count


@frappe.whitelist()
def trigger_rent_reminders():
	"""
	Action button method: triggers rent reminder emails on demand.
	"""
	from airplane_mode.airport_shop_management.tasks import send_rent_reminders
	sent = send_rent_reminders()
	return sent
