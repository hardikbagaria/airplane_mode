// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Contract", {
	refresh(frm) {
		if (!frm.is_new() && ["Active", "Draft"].includes(frm.doc.contract_status)) {
			frm.add_custom_button(__("Generate Rent Schedule"), function() {
				frappe.call({
					method: "airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract.generate_rent_schedule",
					args: {
						contract_name: frm.doc.name
					},
					freeze: true,
					freeze_message: __("Generating rent schedule..."),
					callback: function(r) {
						if (r.message && r.message.length > 0) {
							frappe.msgprint(__("Generated {0} rent payment schedule record(s).", [r.message.length]));
						} else {
							frappe.msgprint(__("Rent schedule is already up to date."));
						}
					}
				});
			}, __("Actions"));
		}

		frm.set_query("tenant", function() {
			return {
				filters: {
					status: "Active"
				}
			};
		});
	},

	onload(frm) {
		if (frm.is_new() && !frm.doc.monthly_rent) {
			frappe.db.get_single_value("Shop Management Settings", "default_rent_amount")
				.then(val => {
					if (val && !frm.doc.monthly_rent) {
						frm.set_value("monthly_rent", val);
					}
				});
		}
	},

	shop(frm) {
		if (frm.doc.shop) {
			frappe.db.get_value("Airport Shop", frm.doc.shop, ["airport", "shop_name", "rent_amount"])
				.then(r => {
					if (r.message) {
						frm.set_value("airport", r.message.airport);
						frm.set_value("shop_name", r.message.shop_name);
						if (!frm.doc.monthly_rent && r.message.rent_amount) {
							frm.set_value("monthly_rent", r.message.rent_amount);
						}
					}
				});
		}
	},

	tenant(frm) {
		if (frm.doc.tenant) {
			frappe.db.get_value("Shop Tenant", frm.doc.tenant, ["tenant_name", "email", "phone", "company_name"])
				.then(r => {
					if (r.message) {
						frm.set_value("tenant_name", r.message.tenant_name);
						frm.set_value("tenant_email", r.message.email);
						frm.set_value("tenant_phone", r.message.phone);
						frm.set_value("company_name", r.message.company_name);
					}
				});
		}
	}
});
