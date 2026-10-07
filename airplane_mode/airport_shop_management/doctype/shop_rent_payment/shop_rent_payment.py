# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import calendar
import datetime
import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, validate_email_address


class ShopRentPayment(Document):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._submitted_shop = self.get("shop")
		self._submitted_tenant = self.get("tenant")
		self._submitted_airport = self.get("airport")

	def validate(self):
		self.validate_contract()
		self.validate_rent_month_format()
		self.validate_rent_month_within_contract()
		self.fetch_and_validate_contract_relationships()
		self.validate_no_duplicate_month_payment()
		self.calculate_due_date()
		self.validate_amounts_and_status()
		self.validate_payment_date()

	def validate_contract(self):
		if not self.contract:
			frappe.throw(_("Contract is required."))
		if not frappe.db.exists("Shop Contract", self.contract):
			frappe.throw(_("Contract {0} does not exist.").format(self.contract))

	def validate_rent_month_format(self):
		if not self.rent_month:
			frappe.throw(_("Rent Month is required."))

		rent_month = str(self.rent_month).strip()
		# Strict YYYY-MM format validation (month must be 01-12)
		pattern = r"^\d{4}-(0[1-9]|1[0-2])$"
		if not re.match(pattern, rent_month):
			frappe.throw(_("Rent Month must be in YYYY-MM format (e.g. 2026-09)."))

		self.rent_month = rent_month

	def validate_rent_month_within_contract(self):
		contract = frappe.get_doc("Shop Contract", self.contract)
		year, month = map(int, self.rent_month.split("-"))
		first_weekday, last_day = calendar.monthrange(year, month)

		month_start = datetime.date(year, month, 1)
		month_end = datetime.date(year, month, last_day)

		contract_start = getdate(contract.contract_start_date)
		contract_end = getdate(contract.contract_end_date)

		if month_start > contract_end or month_end < contract_start:
			frappe.throw(
				_("Rent Month {0} is outside the contract duration ({1} to {2}).").format(
					self.rent_month, contract.contract_start_date, contract.contract_end_date
				)
			)

	def fetch_and_validate_contract_relationships(self):
		contract = frappe.get_doc("Shop Contract", self.contract)

		# Anti-tampering checks: client values must match contract if supplied
		submitted_shop = getattr(self, "_submitted_shop", None) or self.shop
		submitted_tenant = getattr(self, "_submitted_tenant", None) or self.tenant
		submitted_airport = getattr(self, "_submitted_airport", None) or self.airport

		if submitted_shop and submitted_shop != contract.shop:
			frappe.throw(
				_("Rent Payment Shop must match the Shop defined by the selected Contract.")
			)
		if submitted_tenant and submitted_tenant != contract.tenant:
			frappe.throw(
				_("Rent Payment Tenant must match the Tenant defined by the selected Contract.")
			)
		if submitted_airport and submitted_airport != contract.airport:
			frappe.throw(
				_("Rent Payment Airport must match the Airport defined by the selected Contract.")
			)

		# Set authoritative values from contract
		self.shop = contract.shop
		self.tenant = contract.tenant
		self.airport = contract.airport
		self.amount_due = flt(contract.monthly_rent)
		self.tenant_name = contract.tenant_name
		self.tenant_email = contract.tenant_email
		self.shop_name = contract.shop_name
		self.shop_number = frappe.db.get_value("Airport Shop", contract.shop, "shop_number")

	def validate_no_duplicate_month_payment(self):
		duplicate = frappe.db.exists(
			"Shop Rent Payment",
			{
				"contract": self.contract,
				"rent_month": self.rent_month,
				"name": ["!=", self.name or ""],
				"docstatus": ["!=", 2],
			},
		)
		if duplicate:
			frappe.throw(
				_("A rent payment already exists for contract {0} for {1}.").format(
					self.contract, self.rent_month
				)
			)

	def calculate_due_date(self):
		if self.rent_month:
			due = get_rent_due_date(self.rent_month)
			self.due_date = due.strftime("%Y-%m-%d")

	def validate_amounts_and_status(self):
		paid = flt(self.amount_paid)
		due = flt(self.amount_due)

		if paid < 0:
			frappe.throw(_("Amount Paid cannot be negative."))
		if paid > due:
			frappe.throw(_("Amount Paid cannot be greater than Amount Due."))

		# Calculate payment status server-side
		if paid == 0:
			if self.due_date and getdate(today()) > getdate(self.due_date):
				self.payment_status = "Overdue"
			else:
				self.payment_status = "Pending"
		elif 0 < paid < due:
			self.payment_status = "Partially Paid"
		elif paid == due:
			self.payment_status = "Paid"

	def validate_payment_date(self):
		paid = flt(self.amount_paid)
		if paid > 0 and not self.payment_date:
			frappe.throw(_("Payment Date is required when recording a payment."))
		if self.payment_status == "Paid" and not self.payment_date:
			frappe.throw(_("Payment Date is required when the payment status is Paid."))

		if self.payment_date and getdate(self.payment_date) > getdate(today()):
			frappe.throw(_("Payment Date cannot be in the future."))

	def on_submit(self):
		paid = flt(self.amount_paid)
		if paid <= 0:
			frappe.throw(
				_("Cannot submit Rent Receipt with zero payment. Please enter Amount Paid and Payment Date before submitting.")
			)
		if not self.payment_date:
			frappe.throw(_("Payment Date is required when submitting a Rent Receipt."))

		due = flt(self.amount_due)
		if paid >= due:
			self.payment_status = "Paid"
		else:
			self.payment_status = "Partially Paid"
		frappe.db.set_value(
			"Shop Rent Payment", self.name, "payment_status", self.payment_status, update_modified=False
		)

	def on_cancel(self):
		# Revert status on cancellation
		if self.due_date and getdate(today()) > getdate(self.due_date):
			self.payment_status = "Overdue"
		else:
			self.payment_status = "Pending"
		frappe.db.set_value(
			"Shop Rent Payment", self.name, "payment_status", self.payment_status, update_modified=False
		)


def get_following_month(year, month):
	if month == 12:
		return year + 1, 1
	return year, month + 1


def get_rent_generation_date(rent_month):
	"""
	Rent receipt for month YYYY-MM is generated on the 5th of the following month.
	e.g. 2026-09 -> 2026-10-05
	"""
	year, month = map(int, str(rent_month).strip().split("-"))
	next_year, next_month = get_following_month(year, month)
	return datetime.date(next_year, next_month, 5)


def get_rent_due_date(rent_month):
	"""
	Rent receipt for month YYYY-MM is due on the 10th of the following month.
	e.g. 2026-09 -> 2026-10-10
	"""
	year, month = map(int, str(rent_month).strip().split("-"))
	next_year, next_month = get_following_month(year, month)
	return datetime.date(next_year, next_month, 10)


@frappe.whitelist()
def mark_as_paid_and_submit(docname, payment_mode="Bank Transfer", transaction_reference="", payment_date=None):
	"""
	Action button method: records full payment and submits the rent receipt.
	"""
	doc = frappe.get_doc("Shop Rent Payment", docname)
	if doc.docstatus != 0:
		frappe.throw(_("Only Draft Rent Receipts can be marked as paid and submitted."))

	doc.amount_paid = doc.amount_due
	doc.payment_date = payment_date or today()
	doc.payment_mode = payment_mode or "Bank Transfer"
	doc.transaction_reference = transaction_reference or ""
	doc.payment_status = "Paid"
	doc.save()
	doc.submit()
	frappe.db.commit()
	return doc.name


@frappe.whitelist()
def send_receipt_email(docname):
	"""
	Action button method: emails the rent receipt confirmation to tenant.
	"""
	doc = frappe.get_doc("Shop Rent Payment", docname)
	if not doc.tenant_email:
		frappe.throw(_("No tenant email specified for {0}.").format(doc.tenant))

	validate_email_address(doc.tenant_email, throw=True)
	subject = _("Rent Payment Receipt: {0} for {1}").format(doc.shop, doc.rent_month)
	message = f"""
	<p>Dear {doc.tenant_name or doc.tenant},</p>
	<p>Here are the details of your rent receipt for <strong>{doc.shop}</strong> ({doc.airport}).</p>
	<table border="1" cellpadding="8" style="border-collapse: collapse; margin: 15px 0;">
		<tr><td><strong>Receipt Ref</strong></td><td>{doc.name}</td></tr>
		<tr><td><strong>Rent Month</strong></td><td>{doc.rent_month}</td></tr>
		<tr><td><strong>Amount Due</strong></td><td>₹{doc.amount_due:,.2f}</td></tr>
		<tr><td><strong>Amount Paid</strong></td><td>₹{doc.amount_paid:,.2f}</td></tr>
		<tr><td><strong>Payment Status</strong></td><td><strong>{doc.payment_status}</strong></td></tr>
		<tr><td><strong>Payment Date</strong></td><td>{doc.payment_date or 'N/A'}</td></tr>
		<tr><td><strong>Payment Mode</strong></td><td>{doc.payment_mode or 'N/A'}</td></tr>
		<tr><td><strong>Transaction Ref</strong></td><td>{doc.transaction_reference or 'N/A'}</td></tr>
	</table>
	<p>Thank you,<br>Airport Commercial Operations Team</p>
	"""

	frappe.sendmail(
		recipients=[doc.tenant_email],
		subject=subject,
		message=message,
		reference_doctype="Shop Rent Payment",
		reference_name=doc.name,
		now=True,
	)
	frappe.msgprint(_("Receipt sent to {0}.").format(doc.tenant_email))
	return True
