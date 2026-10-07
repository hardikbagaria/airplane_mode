# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = [
		{
			"label": _("Airport"),
			"fieldname": "airport",
			"fieldtype": "Link",
			"options": "Airport",
			"width": 260,
		},
		{
			"label": _("Total Shops"),
			"fieldname": "total_shops",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Occupied"),
			"fieldname": "occupied",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Available"),
			"fieldname": "available",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Under Maintenance"),
			"fieldname": "under_maintenance",
			"fieldtype": "Int",
			"width": 150,
		},
		{
			"label": _("Occupancy Rate"),
			"fieldname": "occupancy_rate",
			"fieldtype": "Percent",
			"width": 130,
		},
	]

	airport_filter = {}
	if filters and filters.get("airport"):
		airport_filter["airport"] = filters.get("airport")

	shops = frappe.get_all(
		"Airport Shop",
		filters=airport_filter,
		fields=["airport", "shop_status"],
	)

	by_airport = {}
	for s in shops:
		ap = s.airport or "Unassigned"
		if ap not in by_airport:
			by_airport[ap] = {
				"airport": ap,
				"total_shops": 0,
				"occupied": 0,
				"available": 0,
				"under_maintenance": 0,
			}
		by_airport[ap]["total_shops"] += 1
		if s.shop_status == "Occupied":
			by_airport[ap]["occupied"] += 1
		elif s.shop_status == "Available":
			by_airport[ap]["available"] += 1
		elif s.shop_status == "Under Maintenance":
			by_airport[ap]["under_maintenance"] += 1

	data = []
	for ap in sorted(by_airport.keys()):
		row = by_airport[ap]
		total = row["total_shops"]
		row["occupancy_rate"] = round((row["occupied"] / total) * 100, 2) if total else 0
		data.append(row)

	return columns, data
