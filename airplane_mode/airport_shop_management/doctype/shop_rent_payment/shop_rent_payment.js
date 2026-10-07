// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

function calculate_rent_due_date(rent_month) {
	if (!rent_month) return null;
	let parts = rent_month.trim().split("-");
	if (parts.length !== 2) return null;
	let y = parseInt(parts[0], 10);
	let m = parseInt(parts[1], 10);
	if (isNaN(y) || isNaN(m) || m < 1 || m > 12) return null;
	let next_y = m === 12 ? y + 1 : y;
	let next_m = m === 12 ? 1 : m + 1;
	let next_m_str = next_m < 10 ? "0" + next_m : "" + next_m;
	return `${next_y}-${next_m_str}-10`;
}

frappe.ui.form.on("Shop Rent Payment", {
	refresh(frm) {
		frm.set_query("contract", function() {
			return {
				filters: {
					contract_status: "Active",
					docstatus: 1
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

		if (!frm.is_new()) {
			// Action: Mark as Paid & Submit (if Draft)
			if (frm.doc.docstatus === 0) {
				frm.add_custom_button(__("Mark as Paid & Submit"), function() {
					let d = new frappe.ui.Dialog({
						title: __("Record Payment & Submit Receipt"),
						fields: [
							{
								label: __("Amount Paid"),
								fieldname: "amount_paid",
								fieldtype: "Currency",
								default: frm.doc.amount_due,
								reqd: 1
							},
							{
								label: __("Payment Date"),
								fieldname: "payment_date",
								fieldtype: "Date",
								default: frappe.datetime.get_today(),
								reqd: 1
							},
							{
								label: __("Payment Mode"),
								fieldname: "payment_mode",
								fieldtype: "Select",
								options: "Bank Transfer\nUPI\nCash\nCheque\nOther",
								default: "Bank Transfer",
								reqd: 1
							},
							{
								label: __("Transaction Reference"),
								fieldname: "transaction_reference",
								fieldtype: "Data"
							}
						],
						primary_action_label: __("Submit Receipt"),
						primary_action: function(values) {
							d.hide();
							frm.set_value("amount_paid", values.amount_paid);
							frm.set_value("payment_date", values.payment_date);
							frm.set_value("payment_mode", values.payment_mode);
							frm.set_value("transaction_reference", values.transaction_reference);
							frm.save("Submit");
						}
					});
					d.show();
				}, __("Actions"));
			}

			// Action: Print Receipt
			frm.add_custom_button(__("Print Rent Receipt"), function() {
				frappe.set_route("print", frm.doc.doctype, frm.doc.name);
			}, __("Actions"));

			// Action: Email Receipt
			if (frm.doc.tenant_email) {
				frm.add_custom_button(__("Send Receipt Email"), function() {
					frappe.call({
						method: "airplane_mode.airport_shop_management.doctype.shop_rent_payment.shop_rent_payment.send_receipt_email",
						args: { docname: frm.doc.name },
						freeze: true,
						freeze_message: __("Sending receipt email..."),
						callback: function() {
							frappe.show_alert({
								message: __("Receipt emailed to {0}", [frm.doc.tenant_email]),
								indicator: "green"
							});
						}
					});
				}, __("Actions"));
			}

			// View Related Docs
			if (frm.doc.contract) {
				frm.add_custom_button(__("View Contract"), function() {
					frappe.set_route("Form", "Shop Contract", frm.doc.contract);
				}, __("Actions"));
			}
			if (frm.doc.shop) {
				frm.add_custom_button(__("View Shop"), function() {
					frappe.set_route("Form", "Airport Shop", frm.doc.shop);
				}, __("Actions"));
			}
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
			let val = frm.doc.rent_month.trim().replace("/", "-");
			let parts = val.split("-");
			if (parts.length === 2 && parts[0].length === 4 && parts[1].length === 1) {
				val = `${parts[0]}-0${parts[1]}`;
				frm.set_value("rent_month", val);
			}
			let computed_due = calculate_rent_due_date(val);
			if (computed_due) {
				frm.set_value("due_date", computed_due);
			}
		}
	},

	amount_paid(frm) {
		let paid = flt(frm.doc.amount_paid);
		let due = flt(frm.doc.amount_due);

		if (paid > 0 && !frm.doc.payment_date) {
			frm.set_value("payment_date", frappe.datetime.get_today());
		}

		if (paid === 0) {
			let today = frappe.datetime.get_today();
			if (frm.doc.due_date && today > frm.doc.due_date) {
				frm.set_value("payment_status", "Overdue");
			} else {
				frm.set_value("payment_status", "Pending");
			}
		} else if (paid > 0 && paid < due) {
			frm.set_value("payment_status", "Partially Paid");
		} else if (paid === due) {
			frm.set_value("payment_status", "Paid");
		}
	}
});
