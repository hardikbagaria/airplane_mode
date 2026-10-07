// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Contract", {
	refresh(frm) {
		// Filter for active tenants
		frm.set_query("tenant", function() {
			return {
				filters: {
					status: "Active"
				}
			};
		});

		// Filter for available shops or current shop
		frm.set_query("shop", function() {
			if (frm.is_new()) {
				return {
					filters: {
						shop_status: "Available"
					}
				};
			}
		});

		// Dynamic Status Badge
		if (!frm.is_new() && frm.doc.contract_status) {
			let color_map = {
				"Active": "green",
				"Draft": "blue",
				"Expired": "orange",
				"Terminated": "red",
				"Cancelled": "gray"
			};
			frm.page.set_indicator(frm.doc.contract_status, color_map[frm.doc.contract_status] || "blue");
		}

		if (!frm.is_new()) {
			// Action: View Rent Receipts
			frm.add_custom_button(__("View Rent Receipts"), function() {
				frappe.set_route("List", "Shop Rent Payment", { contract: frm.doc.name });
			}, __("Actions"));

			// Actions for Submitted / Active contracts
			if (frm.doc.docstatus === 1 && frm.doc.contract_status === "Active") {
				frm.add_custom_button(__("Generate Due Rent Receipts"), function() {
					frappe.call({
						method: "airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract.generate_due_rent_receipts",
						args: { contract_name: frm.doc.name },
						freeze: true,
						freeze_message: __("Generating due rent receipts..."),
						callback: function(r) {
							if (r.message && r.message.length > 0) {
								frappe.msgprint(__("Generated {0} new rent receipt(s).", [r.message.length]));
							} else {
								frappe.msgprint(__("All due rent receipts are already up to date."));
							}
						}
					});
				}, __("Actions"));

				frm.add_custom_button(__("Generate Receipt for Month..."), function() {
					frappe.prompt(
						[
							{
								fieldname: "rent_month",
								fieldtype: "Data",
								label: __("Rent Month (YYYY-MM)"),
								reqd: 1,
								description: __("e.g. 2026-09")
							}
						],
						function(values) {
							frappe.call({
								method: "airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract.generate_rent_receipt_for_month",
								args: {
									contract_name: frm.doc.name,
									rent_month: values.rent_month
								},
								freeze: true,
								callback: function(r) {
									if (r.message) {
										frappe.msgprint(__("Rent receipt {0} created.", [r.message]));
									}
								}
							});
						},
						__("Generate Specific Rent Receipt"),
						__("Generate")
					);
				}, __("Actions"));

				frm.add_custom_button(__("Terminate Contract"), function() {
					frappe.confirm(
						__("Are you sure you want to terminate Contract {0}? This will free up the shop.", [frm.doc.name]),
						function() {
							frappe.call({
								method: "airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract.terminate_contract",
								args: { contract_name: frm.doc.name },
								callback: function(r) {
									frm.reload_doc();
									frappe.show_alert({
										message: __("Contract terminated successfully."),
										indicator: "red"
									});
								}
							});
						}
					);
				}, __("Actions"));

				frm.add_custom_button(__("Renew Contract"), function() {
					frappe.confirm(
						__("Create a new draft renewal contract continuing from this contract?"),
						function() {
							frappe.call({
								method: "airplane_mode.airport_shop_management.doctype.shop_contract.shop_contract.renew_contract",
								args: { contract_name: frm.doc.name },
								callback: function(r) {
									if (r.message) {
										frappe.set_route("Form", "Shop Contract", r.message);
									}
								}
							});
						}
					);
				}, __("Actions"));
			}

			// View Related Docs
			if (frm.doc.shop) {
				frm.add_custom_button(__("View Shop"), function() {
					frappe.set_route("Form", "Airport Shop", frm.doc.shop);
				}, __("Actions"));
			}
			if (frm.doc.tenant) {
				frm.add_custom_button(__("View Tenant"), function() {
					frappe.set_route("Form", "Shop Tenant", frm.doc.tenant);
				}, __("Actions"));
			}
		}
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
