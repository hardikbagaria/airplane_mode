# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ShopType(Document):
	def validate(self):
		if not self.shop_type or not self.shop_type.strip():
			frappe.throw(_("Shop Type name is required."))


def create_default_shop_types():
	"""
	Ensures default Shop Types (Stall, Walk-through, Normal) exist out of the box.
	"""
	default_types = [
		{"shop_type": "Stall", "description": "Small kiosk or booth space in terminal hallways."},
		{"shop_type": "Walk-through", "description": "Open walk-through retail space along passenger pathways."},
		{"shop_type": "Normal", "description": "Standard enclosed retail store unit."},
	]

	for item in default_types:
		if not frappe.db.exists("Shop Type", item["shop_type"]):
			doc = frappe.get_doc({
				"doctype": "Shop Type",
				"shop_type": item["shop_type"],
				"enabled": 1,
				"description": item["description"],
			})
			doc.insert(ignore_permissions=True)

	frappe.db.commit()
