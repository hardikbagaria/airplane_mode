// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Tenant", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.status) {
			let color = frm.doc.status === "Active" ? "green" : "gray";
			frm.page.set_indicator(frm.doc.status, color);
		}
	},

	gstin(frm) {
		if (frm.doc.gstin) {
			frm.set_value("gstin", frm.doc.gstin.trim().toUpperCase());
		}
	}
});
