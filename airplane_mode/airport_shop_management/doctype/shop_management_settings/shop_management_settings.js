// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Management Settings", {
	refresh(frm) {
		// Action: Generate All Due Rent Receipts
		frm.add_custom_button(__("Generate All Due Rent Receipts"), function() {
			frappe.call({
				method: "airplane_mode.airport_shop_management.doctype.shop_management_settings.shop_management_settings.trigger_generate_all_due_receipts",
				freeze: true,
				freeze_message: __("Processing rent receipt generation across all active contracts..."),
				callback: function(r) {
					frappe.msgprint(__("Generated {0} new rent receipt(s).", [r.message || 0]));
				}
			});
		}, __("Actions"));

		// Action: Send Rent Reminders Now
		frm.add_custom_button(__("Send Rent Reminders Now"), function() {
			frappe.call({
				method: "airplane_mode.airport_shop_management.doctype.shop_management_settings.shop_management_settings.trigger_rent_reminders",
				freeze: true,
				freeze_message: __("Sending rent reminder emails..."),
				callback: function(r) {
					frappe.msgprint(__("Sent {0} rent reminder email(s).", [r.message || 0]));
				}
			});
		}, __("Actions"));
	},

	validate(frm) {
		if (frm.doc.default_rent_amount && frm.doc.default_rent_amount <= 0) {
			frappe.msgprint(__("Default Rent Amount must be greater than 0."));
			frappe.validated = false;
		}
	}
});
