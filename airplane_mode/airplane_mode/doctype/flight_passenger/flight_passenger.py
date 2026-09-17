# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FlightPassenger(Document):

    def before_save(self):
        if self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        else:
            self.full_name = self.first_name