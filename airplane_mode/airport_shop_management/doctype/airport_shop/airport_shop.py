# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class AirportShop(Document):
	def autoname(self):
		if not self.name and self.airport and self.shop_number:
			airport_code = frappe.db.get_value("Airport", self.airport, "code") or self.airport
			self.name = f"{airport_code}-{self.shop_number}"

	def validate(self):
		self.validate_mandatory_fields()
		self.validate_area()
		self.validate_status()
		self.validate_unique_shop_number()
		self.initialize_default_rent()
		self.validate_contract_status_consistency()

	def validate_mandatory_fields(self):
		if not self.shop_number:
			frappe.throw(_("Shop Number is required."))
		if not self.shop_name:
			frappe.throw(_("Shop Name is required."))
		if not self.airport:
			frappe.throw(_("Airport is required."))

	def validate_area(self):
		if flt(self.area) <= 0:
			frappe.throw(_("Area must be greater than 0."))

	def validate_status(self):
		valid_statuses = ["Available", "Occupied", "Under Maintenance"]
		if self.shop_status not in valid_statuses:
			frappe.throw(_("Shop Status must be one of: {0}.").format(", ".join(valid_statuses)))

	def validate_unique_shop_number(self):
		if self.is_new():
			duplicate = frappe.db.exists(
				"Airport Shop",
				{
					"airport": self.airport,
					"shop_number": self.shop_number,
				},
			)
		else:
			duplicate = frappe.db.exists(
				"Airport Shop",
				{
					"airport": self.airport,
					"shop_number": self.shop_number,
					"name": ["!=", self.name],
				},
			)
		if duplicate:
			frappe.throw(
				_("Shop {0} already exists in {1}.").format(self.shop_number, self.airport)
			)

	def initialize_default_rent(self):
		if self.is_new() and (self.rent_amount is None or self.rent_amount == ""):
			default_rent = frappe.db.get_single_value(
				"Shop Management Settings", "default_rent_amount"
			)
			if default_rent and flt(default_rent) > 0:
				self.rent_amount = flt(default_rent)

	def validate_contract_status_consistency(self):
		if not self.name or self.is_new():
			if self.shop_status == "Occupied":
				frappe.throw(_("Shop cannot be marked as Occupied without an active contract."))
			self.current_contract = None
			self.current_tenant = None
			return

		active_contract = frappe.db.get_value(
			"Shop Contract",
			{"shop": self.name, "contract_status": "Active"},
			["name", "tenant"],
			as_dict=True,
		)
		if active_contract:
			if self.shop_status == "Available":
				frappe.throw(
					_("Shop has an active contract ({0}) and cannot be marked as Available.").format(
						active_contract.name
					)
				)
			self.shop_status = "Occupied"
			self.current_contract = active_contract.name
			self.current_tenant = active_contract.tenant
		else:
			if self.shop_status == "Occupied":
				frappe.throw(_("Shop cannot be marked as Occupied without an active contract."))
			self.current_contract = None
			self.current_tenant = None


@frappe.whitelist()
def get_shop_statistics(airport=None):
	"""
	Returns airport-level shop statistics:
	Total Shops, Occupied, Available, Under Maintenance.
	"""
	filters = {}
	if airport:
		filters["airport"] = airport

	shops = frappe.get_all(
		"Airport Shop",
		filters=filters,
		fields=["airport", "shop_status"],
	)

	stats = {
		"total": len(shops),
		"occupied": sum(1 for s in shops if s.shop_status == "Occupied"),
		"available": sum(1 for s in shops if s.shop_status == "Available"),
		"under_maintenance": sum(1 for s in shops if s.shop_status == "Under Maintenance"),
	}

	if not airport:
		by_airport = {}
		for s in shops:
			ap = s.airport
			if ap not in by_airport:
				by_airport[ap] = {"total": 0, "occupied": 0, "available": 0, "under_maintenance": 0}
			by_airport[ap]["total"] += 1
			if s.shop_status == "Occupied":
				by_airport[ap]["occupied"] += 1
			elif s.shop_status == "Available":
				by_airport[ap]["available"] += 1
			elif s.shop_status == "Under Maintenance":
				by_airport[ap]["under_maintenance"] += 1
		stats["by_airport"] = by_airport

	return stats
