// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt
frappe.ui.form.on("Airport Shop", {
	refresh(frm) {
		// Filter shop_type to only show enabled types
		frm.set_query("shop_type", function() {
			return {
				filters: {
					enabled: 1
				}
			};
		});

		if (!frm.is_new() && frm.doc.shop_status) {
			let indicator_map = {
				"Available": "green",
				"Occupied": "red",
				"Under Maintenance": "orange"
			};
			frm.page.set_indicator(frm.doc.shop_status, indicator_map[frm.doc.shop_status] || "blue");
		}

		if (!frm.is_new()) {
			// Action: Create Contract
			if (frm.doc.shop_status === "Available") {
				frm.add_custom_button(__("Create Contract"), function() {
					frappe.new_doc("Shop Contract", {
						shop: frm.doc.name,
						airport: frm.doc.airport,
						monthly_rent: frm.doc.rent_amount
					});
				}, __("Actions"));
			}

			// Action: View Contracts
			frm.add_custom_button(__("View Contracts"), function() {
				frappe.set_route("List", "Shop Contract", { shop: frm.doc.name });
			}, __("Actions"));

			// Action: View Rent Receipts
			frm.add_custom_button(__("View Rent Receipts"), function() {
				frappe.set_route("List", "Shop Rent Payment", { shop: frm.doc.name });
			}, __("Actions"));

			// Action: View Leads
			frm.add_custom_button(__("View Leads"), function() {
				frappe.set_route("List", "Shop Lead", { shop: frm.doc.name });
			}, __("Actions"));

			// Action: Toggle Maintenance
			if (frm.doc.shop_status !== "Occupied") {
				let toggle_label = frm.doc.shop_status === "Available" ? __("Set Under Maintenance") : __("Set Available");
				frm.add_custom_button(toggle_label, function() {
					frappe.call({
						method: "airplane_mode.airport_shop_management.doctype.airport_shop.airport_shop.toggle_maintenance",
						args: { shop_name: frm.doc.name },
						callback: function(r) {
							frm.reload_doc();
							frappe.show_alert({
								message: __("Shop status updated to {0}", [r.message]),
								indicator: r.message === "Available" ? "green" : "orange"
							});
						}
					});
				}, __("Actions"));
			}
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
