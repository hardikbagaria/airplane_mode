# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import datetime
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class ShopContract(Document):
	def before_insert(self):
		if not self.contract_status:
			self.contract_status = "Draft"

	def validate(self):
		self.validate_mandatory_fields()
		self.validate_dates()
		self.validate_monthly_rent()
		self.validate_security_deposit()
		self.validate_status_and_frequency()
		self.fetch_and_validate_shop_details()
		self.fetch_and_validate_tenant_details()
		self.validate_no_overlapping_active_contracts()
		self.validate_shortening_against_paid_records()

	def validate_mandatory_fields(self):
		if not self.shop:
			frappe.throw(_("Shop is required."))
		if not self.tenant:
			frappe.throw(_("Tenant is required."))
		if not self.contract_start_date:
			frappe.throw(_("Contract Start Date is required."))
		if not self.contract_end_date:
			frappe.throw(_("Contract End Date is required."))

	def validate_dates(self):
		if getdate(self.contract_end_date) <= getdate(self.contract_start_date):
			frappe.throw(_("Contract End Date must be after Contract Start Date."))

	def validate_monthly_rent(self):
		if self.is_new() and (self.monthly_rent is None or self.monthly_rent == ""):
			default_rent = frappe.db.get_single_value(
				"Shop Management Settings", "default_rent_amount"
			)
			if default_rent and flt(default_rent) > 0:
				self.monthly_rent = flt(default_rent)

		if self.monthly_rent is None or flt(self.monthly_rent) <= 0:
			frappe.throw(_("Monthly Rent must be greater than 0."))

	def validate_security_deposit(self):
		if flt(self.security_deposit) < 0:
			frappe.throw(_("Security Deposit cannot be negative."))

	def validate_status_and_frequency(self):
		valid_freqs = ["Monthly", "Quarterly", "Half-Yearly", "Yearly"]
		if self.payment_frequency not in valid_freqs:
			frappe.throw(_("Payment Frequency must be one of: {0}.").format(", ".join(valid_freqs)))

		valid_statuses = ["Draft", "Active", "Expired", "Terminated", "Cancelled"]
		if self.contract_status not in valid_statuses:
			frappe.throw(_("Contract Status must be one of: {0}.").format(", ".join(valid_statuses)))

	def fetch_and_validate_shop_details(self):
		shop = frappe.get_doc("Airport Shop", self.shop)
		self.airport = shop.airport
		self.shop_name = shop.shop_name

	def fetch_and_validate_tenant_details(self):
		tenant = frappe.get_doc("Shop Tenant", self.tenant)
		if tenant.status != "Active":
			frappe.throw(_("Selected Tenant {0} is Inactive.").format(self.tenant))
		self.tenant_name = tenant.tenant_name
		self.tenant_email = tenant.email
		self.tenant_phone = tenant.phone
		self.company_name = tenant.company_name

	def validate_no_overlapping_active_contracts(self):
		# Only active submitted contracts enforce exclusivity
		if self.contract_status != "Active" and self.docstatus != 1:
			return

		overlapping = frappe.db.sql(
			"""
			SELECT name, contract_start_date, contract_end_date
			FROM `tabShop Contract`
			WHERE shop = %(shop)s
			  AND name != %(name)s
			  AND docstatus = 1
			  AND contract_status = 'Active'
			  AND contract_start_date <= %(end_date)s
			  AND contract_end_date >= %(start_date)s
			""",
			{
				"shop": self.shop,
				"name": self.name or "",
				"start_date": self.contract_start_date,
				"end_date": self.contract_end_date,
			},
			as_dict=True,
		)
		if overlapping:
			frappe.throw(
				_("Shop {0} already has an overlapping active contract ({1}).").format(
					self.shop, overlapping[0].name
				)
			)

	def validate_shortening_against_paid_records(self):
		if self.is_new():
			return

		months = get_months_in_range(self.contract_start_date, self.contract_end_date)
		paid_outside = frappe.db.sql(
			"""
			SELECT name, rent_month, amount_paid
			FROM `tabShop Rent Payment`
			WHERE contract = %(contract)s
			  AND amount_paid > 0
			  AND docstatus != 2
			  AND rent_month NOT IN %(months)s
			""",
			{
				"contract": self.name,
				"months": tuple(months) if months else ("__none__",),
			},
			as_dict=True,
		)
		if paid_outside:
			frappe.throw(
				_(
					"Cannot shorten contract duration because paid rent records exist for months outside the new date range."
				)
			)

	def on_submit(self):
		self.contract_status = "Active"
		frappe.db.set_value("Shop Contract", self.name, "contract_status", "Active", update_modified=False)
		sync_shop_lease_status(self.shop)
		# Generate due rent receipts up to current billing date
		generate_due_rent_receipts(self.name)

	def on_cancel(self):
		# Prevent cancellation if submitted paid rent payments exist
		paid_payments = frappe.db.exists(
			"Shop Rent Payment",
			{"contract": self.name, "docstatus": 1, "amount_paid": [">", 0]}
		)
		if paid_payments:
			frappe.throw(
				_("Cannot cancel Contract {0} because submitted paid rent receipts exist. Cancel those receipts first.").format(
					self.name
				)
			)

		# Delete unpaid draft rent payment records
		frappe.db.delete(
			"Shop Rent Payment",
			{"contract": self.name, "docstatus": 0, "amount_paid": 0}
		)

		self.contract_status = "Cancelled"
		frappe.db.set_value("Shop Contract", self.name, "contract_status", "Cancelled", update_modified=False)
		sync_shop_lease_status(self.shop, exclude_contract=self.name)

	def on_trash(self):
		sync_shop_lease_status(self.shop, exclude_contract=self.name)


def sync_shop_lease_status(shop_name, exclude_contract=None):
	"""
	Synchronizes Airport Shop status and current_contract/current_tenant
	based on active submitted contracts in the database.
	"""
	if not shop_name or not frappe.db.exists("Airport Shop", shop_name):
		return

	filters = {"shop": shop_name, "contract_status": "Active", "docstatus": 1}
	if exclude_contract:
		filters["name"] = ["!=", exclude_contract]

	active_contract = frappe.db.get_value(
		"Shop Contract",
		filters,
		["name", "tenant"],
		as_dict=True,
	)
	current_status = frappe.db.get_value("Airport Shop", shop_name, "shop_status")

	if active_contract:
		frappe.db.set_value(
			"Airport Shop",
			shop_name,
			{
				"shop_status": "Occupied",
				"current_contract": active_contract.name,
				"current_tenant": active_contract.tenant,
			},
			update_modified=False,
		)
	else:
		new_status = "Under Maintenance" if current_status == "Under Maintenance" else "Available"
		frappe.db.set_value(
			"Airport Shop",
			shop_name,
			{
				"shop_status": new_status,
				"current_contract": None,
				"current_tenant": None,
			},
			update_modified=False,
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


def get_months_in_range(start_date, end_date):
	"""
	Returns list of 'YYYY-MM' strings between start_date and end_date inclusive.
	"""
	start = getdate(start_date)
	end = getdate(end_date)
	months = []
	curr = datetime.date(start.year, start.month, 1)
	end_month_first = datetime.date(end.year, end.month, 1)

	while curr <= end_month_first:
		months.append(curr.strftime("%Y-%m"))
		year = curr.year + (1 if curr.month == 12 else 0)
		month = 1 if curr.month == 12 else curr.month + 1
		curr = datetime.date(year, month, 1)

	return months


@frappe.whitelist()
def generate_due_rent_receipts(contract_name):
	"""
	Generates Shop Rent Payment records for any contract month where
	the generation date (5th of the following month) has arrived (<= today).
	Idempotent: does not create duplicates.
	"""
	contract = frappe.get_doc("Shop Contract", contract_name)
	if contract.docstatus == 2 or contract.contract_status not in ["Active", "Draft"]:
		return []

	months = get_months_in_range(contract.contract_start_date, contract.contract_end_date)
	created_payments = []
	current_date = getdate(today())

	for rent_month in months:
		gen_date = get_rent_generation_date(rent_month)
		if current_date < gen_date:
			continue

		existing = frappe.db.exists(
			"Shop Rent Payment",
			{"contract": contract.name, "rent_month": rent_month, "docstatus": ["!=", 2]},
		)
		if not existing:
			due_date = get_rent_due_date(rent_month)
			status = "Overdue" if current_date > due_date else "Pending"
			payment = frappe.get_doc(
				{
					"doctype": "Shop Rent Payment",
					"contract": contract.name,
					"shop": contract.shop,
					"tenant": contract.tenant,
					"airport": contract.airport,
					"rent_month": rent_month,
					"due_date": due_date.strftime("%Y-%m-%d"),
					"amount_due": flt(contract.monthly_rent),
					"amount_paid": 0,
					"payment_status": status,
					"docstatus": 0,
				}
			)
			payment.insert(ignore_permissions=True)
			created_payments.append(payment.name)

	frappe.db.commit()
	return created_payments


@frappe.whitelist()
def generate_rent_receipt_for_month(contract_name, rent_month):
	"""
	Allows generating a rent receipt for a specific contract month on demand.
	"""
	contract = frappe.get_doc("Shop Contract", contract_name)
	months = get_months_in_range(contract.contract_start_date, contract.contract_end_date)
	if rent_month not in months:
		frappe.throw(_("Month {0} is outside contract duration.").format(rent_month))

	existing = frappe.db.exists(
		"Shop Rent Payment",
		{"contract": contract.name, "rent_month": rent_month, "docstatus": ["!=", 2]},
	)
	if existing:
		frappe.throw(_("A rent receipt already exists for {0}.").format(rent_month))

	due_date = get_rent_due_date(rent_month)
	current_date = getdate(today())
	status = "Overdue" if current_date > due_date else "Pending"

	payment = frappe.get_doc(
		{
			"doctype": "Shop Rent Payment",
			"contract": contract.name,
			"shop": contract.shop,
			"tenant": contract.tenant,
			"airport": contract.airport,
			"rent_month": rent_month,
			"due_date": due_date.strftime("%Y-%m-%d"),
			"amount_due": flt(contract.monthly_rent),
			"amount_paid": 0,
			"payment_status": status,
			"docstatus": 0,
		}
	)
	payment.insert(ignore_permissions=True)
	frappe.db.commit()
	return payment.name


@frappe.whitelist()
def terminate_contract(contract_name):
	"""
	Action button method to formally terminate an active contract.
	"""
	contract = frappe.get_doc("Shop Contract", contract_name)
	if contract.contract_status == "Terminated":
		frappe.throw(_("Contract is already terminated."))

	contract.contract_status = "Terminated"
	contract.save(ignore_permissions=True)
	sync_shop_lease_status(contract.shop)
	frappe.db.commit()
	return contract.contract_status


@frappe.whitelist()
def renew_contract(contract_name):
	"""
	Action button method to create a new draft renewal contract.
	"""
	contract = frappe.get_doc("Shop Contract", contract_name)
	old_end = getdate(contract.contract_end_date)
	new_start = old_end + datetime.timedelta(days=1)
	new_end = datetime.date(new_start.year + 1, new_start.month, new_start.day) - datetime.timedelta(days=1)

	new_doc = frappe.get_doc(
		{
			"doctype": "Shop Contract",
			"shop": contract.shop,
			"tenant": contract.tenant,
			"monthly_rent": contract.monthly_rent,
			"security_deposit": contract.security_deposit,
			"payment_frequency": contract.payment_frequency,
			"contract_start_date": new_start.strftime("%Y-%m-%d"),
			"contract_end_date": new_end.strftime("%Y-%m-%d"),
			"contract_status": "Draft",
			"docstatus": 0,
		}
	)
	new_doc.insert()
	frappe.db.commit()
	return new_doc.name
