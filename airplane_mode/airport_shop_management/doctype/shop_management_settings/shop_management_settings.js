// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Management Settings", {
	validate(frm) {
		if (frm.doc.default_rent_amount && frm.doc.default_rent_amount <= 0) {
			frappe.msgprint(__("Default Rent Amount must be greater than 0."));
			frappe.validated = false;
		}
	}
});
