# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from airplane_mode.www.shops import detail


def get_context(context):
	if not frappe.form_dict.get("shop") and frappe.form_dict.get("name"):
		frappe.form_dict["shop"] = frappe.form_dict.get("name")
	detail.get_context(context)
