// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Tenant", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.status) {
			let color = frm.doc.status === "Active" ? "green" : "gray";
			frm.page.set_indicator(frm.doc.status, color);
		}

		if (!frm.is_new()) {
			// Action: Create Contract
			if (frm.doc.status === "Active") {
				frm.add_custom_button(__("Create Contract"), function() {
					frappe.new_doc("Shop Contract", {
						tenant: frm.doc.name
					});
				}, __("Actions"));
			}

			// Action: View Contracts
			frm.add_custom_button(__("View Contracts"), function() {
				frappe.set_route("List", "Shop Contract", { tenant: frm.doc.name });
			}, __("Actions"));

			// Action: View Rent Receipts
			frm.add_custom_button(__("View Rent Receipts"), function() {
				frappe.set_route("List", "Shop Rent Payment", { tenant: frm.doc.name });
			}, __("Actions"));
		}
	},

	gstin(frm) {
		if (frm.doc.gstin) {
			frm.set_value("gstin", frm.doc.gstin.trim().toUpperCase());
		}
	}
});
