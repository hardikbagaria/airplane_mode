// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Lead", {
	refresh(frm) {
		frm.set_query("shop", function() {
			return {
				filters: {
					shop_status: "Available"
				}
			};
		});
	},

	shop(frm) {
		if (frm.doc.shop) {
			frappe.db.get_value("Airport Shop", frm.doc.shop, ["airport", "shop_number", "shop_name"])
				.then(r => {
					if (r.message) {
						frm.set_value("airport", r.message.airport);
						frm.set_value("shop_number", r.message.shop_number);
						frm.set_value("shop_name", r.message.shop_name);
					}
				});
		}
	}
});
