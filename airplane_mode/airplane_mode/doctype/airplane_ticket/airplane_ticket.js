// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airplane Ticket", {
    flight_price(frm) {
        calculate_total_amount(frm);
    },
    validate(frm){
           let types = [];
        frm.doc.add_ons.forEach(row => {
            if (types.includes(row.item)) {
                frappe.throw(
                    `Add-on Type ${row.item} can only be added once.`
                );
            }
            types.push(row.item);
        });
    }
});

frappe.ui.form.on("Airplane Ticket Add-on Item", {
    amount(frm,cdt,cdn){
        console.log(cdt,cdn);
        calculate_total_amount(frm);
    }
});

function calculate_total_amount(frm) {
    let total = frm.doc.flight_price || 0;

    (frm.doc.add_ons || []).forEach(row => {
        total += row.amount || 0;
    });

    frm.set_value("total_amount", total);
}