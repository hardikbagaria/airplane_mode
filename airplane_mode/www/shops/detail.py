# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_context(context):
	context.no_cache = 1

	shop_name = frappe.form_dict.get("shop")
	if not shop_name:
		frappe.local.flags.redirect_location = "/shops"
		raise frappe.Redirect

	if not frappe.db.exists("Airport Shop", shop_name):
		frappe.throw(_("Shop not found"), frappe.DoesNotExistError)

	# Fetch safe public-facing information
	shop = frappe.get_doc("Airport Shop", shop_name)
	context.shop = {
		"name": shop.name,
		"shop_number": shop.shop_number,
		"shop_name": shop.shop_name,
		"airport": shop.airport,
		"area": shop.area,
		"rent_amount": shop.rent_amount,
		"shop_status": shop.shop_status,
		"description": shop.description,
	}

	context.airport = frappe.db.get_value(
		"Airport", shop.airport, ["name", "code", "city", "country"], as_dict=True
	)
	context.title = f"Shop #{shop.shop_number} - {shop.shop_name or shop.airport}"
