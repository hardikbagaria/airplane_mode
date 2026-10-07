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

		// Dynamic Status Badge
		if (!frm.is_new() && frm.doc.status) {
			let color_map = {
				"New": "blue",
				"Contacted": "orange",
				"Converted": "green",
				"Rejected": "red"
			};
			frm.page.set_indicator(frm.doc.status, color_map[frm.doc.status] || "blue");
		}

		if (!frm.is_new()) {
			if (frm.doc.status !== "Converted") {
				// Action: Convert to Tenant
				frm.add_custom_button(__("Convert to Tenant"), function() {
					frappe.confirm(
						__("Convert lead '{0}' into a new Shop Tenant record?", [frm.doc.name1]),
						function() {
							frappe.call({
								method: "airplane_mode.airport_shop_management.doctype.shop_lead.shop_lead.convert_to_tenant",
								args: { lead_name: frm.doc.name },
								freeze: true,
								callback: function(r) {
									if (r.message) {
										frappe.show_alert({
											message: __("Tenant '{0}' created.", [r.message]),
											indicator: "green"
										});
										frappe.set_route("Form", "Shop Tenant", r.message);
									}
								}
							});
						}
					);
				}, __("Actions"));

				// Action: Create Contract
				if (frm.doc.shop) {
					frm.add_custom_button(__("Create Contract"), function() {
						frappe.new_doc("Shop Contract", {
							shop: frm.doc.shop,
							airport: frm.doc.airport
						});
					}, __("Actions"));
				}

				// Status Quick Actions
				if (frm.doc.status === "New") {
					frm.add_custom_button(__("Mark Contacted"), function() {
						frm.set_value("status", "Contacted");
						frm.save();
					}, __("Actions"));
				}

				frm.add_custom_button(__("Mark Rejected"), function() {
					frm.set_value("status", "Rejected");
					frm.save();
				}, __("Actions"));
			}

			if (frm.doc.shop) {
				frm.add_custom_button(__("View Shop"), function() {
					frappe.set_route("Form", "Airport Shop", frm.doc.shop);
				}, __("Actions"));
			}
		}
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
