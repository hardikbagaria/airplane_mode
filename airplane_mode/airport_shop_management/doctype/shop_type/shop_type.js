// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Type", {
	refresh(frm) {
		if (!frm.is_new()) {
			let indicator_color = frm.doc.enabled ? "green" : "gray";
			let indicator_label = frm.doc.enabled ? __("Enabled") : __("Disabled");
			frm.page.set_indicator(indicator_label, indicator_color);

			// Action: View Shops with this type
			frm.add_custom_button(__("View Shops"), function() {
				frappe.set_route("List", "Airport Shop", { shop_type: frm.doc.name });
			}, __("Actions"));

			// Action: Toggle Enabled
			let toggle_label = frm.doc.enabled ? __("Disable") : __("Enable");
			frm.add_custom_button(toggle_label, function() {
				frm.set_value("enabled", frm.doc.enabled ? 0 : 1);
				frm.save();
			}, __("Actions"));
		}
	}
});
