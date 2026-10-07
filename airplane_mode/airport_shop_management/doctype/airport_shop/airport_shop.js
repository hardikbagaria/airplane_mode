// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airport Shop", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.shop_status) {
			let indicator_map = {
				"Available": "green",
				"Occupied": "red",
				"Under Maintenance": "orange"
			};
			frm.page.set_indicator(frm.doc.shop_status, indicator_map[frm.doc.shop_status] || "blue");
		}
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.rent_amount) {
			frappe.db.get_single_value("Shop Management Settings", "default_rent_amount")
				.then(val => {
					if (val && !frm.doc.rent_amount) {
						frm.set_value("rent_amount", val);
					}
				});
		}
	}
});
