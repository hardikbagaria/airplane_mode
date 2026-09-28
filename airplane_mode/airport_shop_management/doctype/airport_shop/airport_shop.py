# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AirportShop(Document):

    def validate(self):
        existing_shop = frappe.db.exists(
            "Airport Shop",
            {
                "airport": self.airport,
                "shop_no": self.shop_no,
                "name": ["!=", self.name]
            }
        )

        if existing_shop:
            frappe.throw(
                f"Shop {self.shop_no} already exists at this airport."
            )