// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.query_reports["Airport Shop Statistics"] = {
	"filters": [
		{
			"fieldname": "airport",
			"label": __("Airport"),
			"fieldtype": "Link",
			"options": "Airport"
		}
	]
};
