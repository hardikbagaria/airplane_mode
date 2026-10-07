# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, today, validate_email_address


def send_rent_reminders():
	"""
	Daily scheduler task that sends rent reminders to tenants
	for Pending and Overdue payments.
	Respects the 'enable_rent_reminders' toggle in Shop Management Settings.
	Avoids repeated spam by not sending more than once per day.
	"""
	enable_reminders = frappe.db.get_single_value(
		"Shop Management Settings", "enable_rent_reminders"
	)
	if not enable_reminders:
		return 0

	current_date = getdate(today())

	# Find Pending and Overdue payments
	payments = frappe.get_all(
		"Shop Rent Payment",
		filters={
			"payment_status": ["in", ["Pending", "Overdue"]],
		},
		fields=[
			"name",
			"contract",
			"shop",
			"airport",
			"tenant",
			"rent_month",
			"amount_due",
			"amount_paid",
			"due_date",
			"payment_status",
			"last_reminder_sent",
		],
	)

	sent_count = 0
	for p in payments:
		# Avoid repeated spam: do not send if already sent today
		if p.last_reminder_sent and getdate(p.last_reminder_sent) >= current_date:
			continue

		tenant_email = frappe.db.get_value("Shop Tenant", p.tenant, "email")
		tenant_name = frappe.db.get_value("Shop Tenant", p.tenant, "tenant_name") or p.tenant
		shop_doc = (
			frappe.db.get_value(
				"Airport Shop", p.shop, ["shop_number", "shop_name"], as_dict=True
			)
			or {}
		)
		shop_title = f"{shop_doc.get('shop_name', p.shop)} (#{shop_doc.get('shop_number', '')})"

		if not tenant_email:
			continue

		try:
			validate_email_address(tenant_email)
		except Exception:
			continue

		subject = _("Rent Reminder: {0} for {1}").format(p.shop, p.rent_month)
		message = f"""
		<p>Dear {tenant_name},</p>
		<p>This is a reminder regarding the rent payment for your airport shop space.</p>
		<table border="1" cellpadding="8" style="border-collapse: collapse; margin: 15px 0;">
			<tr><td><strong>Airport</strong></td><td>{p.airport}</td></tr>
			<tr><td><strong>Shop</strong></td><td>{shop_title}</td></tr>
			<tr><td><strong>Rent Month</strong></td><td>{p.rent_month}</td></tr>
			<tr><td><strong>Amount Due</strong></td><td>₹{p.amount_due:,.2f}</td></tr>
			<tr><td><strong>Due Date</strong></td><td>{p.due_date}</td></tr>
			<tr><td><strong>Payment Status</strong></td><td><strong>{p.payment_status}</strong></td></tr>
		</table>
		<p>Please make the payment at your earliest convenience.</p>
		<p>Best regards,<br>Airport Commercial Operations Team</p>
		"""

		try:
			frappe.sendmail(
				recipients=[tenant_email],
				subject=subject,
				message=message,
				reference_doctype="Shop Rent Payment",
				reference_name=p.name,
				now=True,
			)
			frappe.db.set_value(
				"Shop Rent Payment", p.name, "last_reminder_sent", current_date, update_modified=False
			)
			sent_count += 1
		except Exception as e:
			frappe.log_error(f"Failed to send rent reminder for {p.name}: {e}", "Shop Rent Reminder")

	frappe.db.commit()
	return sent_count
