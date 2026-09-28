// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airport Shop", {
    async before_save(frm) {
        const result = await frappe.db.get_value(
            "Airport Shop",
            {
                airport: frm.doc.airport,
                shop_no: frm.doc.shop_no,
                name: ["!=", frm.doc.name]
            },
            "name"
        );

        if (result.message && result.message.name) {
            frappe.throw(
                `Shop ${frm.doc.shop_no} already exists at this airport.`
            );
        }
    },
});
