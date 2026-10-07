// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shop Rent Payment", {
	refresh(frm) {
		frm.set_query("contract", function() {
			return {
				filters: {
					contract_status: ["in", ["Active", "Draft"]]
				}
			};
		});

		// Dynamic status badge indicator
		if (!frm.is_new() && frm.doc.payment_status) {
			let indicator_map = {
				"Paid": "green",
				"Partially Paid": "orange",
				"Pending": "yellow",
				"Overdue": "red"
			};
			let color = indicator_map[frm.doc.payment_status] || "blue";
			frm.page.set_indicator(frm.doc.payment_status, color);
		}
	},

	contract(frm) {
		if (frm.doc.contract) {
			frappe.db.get_value("Shop Contract", frm.doc.contract, [
				"shop", "airport", "shop_name", "tenant", "tenant_name", "tenant_email", "monthly_rent"
			]).then(r => {
				if (r.message) {
					frm.set_value("shop", r.message.shop);
					frm.set_value("airport", r.message.airport);
					frm.set_value("shop_name", r.message.shop_name);
					frm.set_value("tenant", r.message.tenant);
					frm.set_value("tenant_name", r.message.tenant_name);
					frm.set_value("tenant_email", r.message.tenant_email);
					frm.set_value("amount_due", r.message.monthly_rent);

					if (r.message.shop) {
						frappe.db.get_value("Airport Shop", r.message.shop, "shop_number")
							.then(res => {
								if (res.message) {
									frm.set_value("shop_number", res.message.shop_number);
								}
							});
					}
				}
			});
		}
	},

	rent_month(frm) {
		if (frm.doc.rent_month) {
			let val = frm.doc.rent_month.trim();
			// Help auto-correct common input errors (e.g. 2026/09 or 2026-9)
			val = val.replace("/", "-");
			let parts = val.split("-");
			if (parts.length === 2 && parts[0].length === 4 && parts[1].length === 1) {
				val = `${parts[0]}-0${parts[1]}`;
				frm.set_value("rent_month", val);
			}
			frm.set_value("due_date", `${val}-01`);
		}
	},

	amount_paid(frm) {
		let paid = flt(frm.doc.amount_paid);
		let due = flt(frm.doc.amount_due);

		if (paid > 0 && !frm.doc.payment_date) {
			frm.set_value("payment_date", frappe.datetime.get_today());
		}

		if (paid === 0) {
			frm.set_value("payment_status", "Pending");
		} else if (paid > 0 && paid < due) {
			frm.set_value("payment_status", "Partially Paid");
		} else if (paid === due) {
			frm.set_value("payment_status", "Paid");
		}
	}
});
