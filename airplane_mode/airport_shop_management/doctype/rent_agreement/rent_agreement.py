# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RentAgreement(Document):

    def validate(self):
        self.validate_airport_shop()

    def validate_airport_shop(self):

        # Check if Airport Shop is rentable
        is_rentable = frappe.db.get_value(
            "Airport Shop",
            self.airport_shop,
            "is_rentable"
        )

        if not is_rentable:
            frappe.throw(
                f"Airport Shop {self.airport_shop} is not rentable."
            )

        # Check if already rented
        existing = frappe.db.sql("""
            SELECT name, date_of_expiry
            FROM `tabRent Agreement`
            WHERE airport_shop = %s
              AND docstatus = 1
              AND date_of_expiry >= CURDATE()
              AND name != %s
            LIMIT 1
        """, (self.airport_shop, self.name), as_dict=True)

        if existing:
            frappe.throw(
                f"Airport Shop {self.airport_shop} is already rented "
                f"until {existing[0].date_of_expiry}."
            )