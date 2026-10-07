# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe


def get_context(context):
	context.no_cache = 1
	context.title = "Airport Shops Directory | Commercial Leasing"

	selected_airport = frappe.form_dict.get("airport")
	filters = {}
	if selected_airport:
		filters["airport"] = selected_airport

	# Only fetch safe, public-facing information
	context.shops = frappe.get_all(
		"Airport Shop",
		filters=filters,
		fields=[
			"name",
			"shop_number",
			"shop_name",
			"airport",
			"area",
			"rent_amount",
			"shop_status",
			"description",
		],
		order_by="shop_number asc",
	)

	context.airports = frappe.get_all("Airport", fields=["name", "code", "city"])
	context.selected_airport = selected_airport
