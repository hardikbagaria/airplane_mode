# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import calendar
import datetime
import re
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


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
			frappe.throw(_("Rent Month must be in YYYY-MM format."))

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
			self.due_date = f"{self.rent_month}-01"

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
