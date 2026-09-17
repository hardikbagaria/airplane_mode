# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
import random

class AirplaneTicket(Document):
    def before_insert(self):
        number = random.randint(1, 99)

        letters = ["A", "B", "C", "D", "E"]
        letter = random.choice(letters)

        self.seat = str(number) + letter
    def before_submit(self):
        if self.status != "Boarded":
            frappe.throw("Airplane Ticket can only be submitted when the status is Boarded.")

    def validate(self):
        self.calculate_total_amount()
        types = []

        for row in self.add_ons:
            if row.item in types:
                frappe.throw(f"Add-on Type {row.item} can only be added once.")
            types.append(row.item)

    def calculate_total_amount(self):
        total = self.flight_price or 0

        for add_on in self.add_ons:
            total += add_on.amount or 0

        self.total_amount = total
    