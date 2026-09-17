import frappe
import random


def execute():
    tickets = frappe.get_all(
        "Airplane Ticket",
        filters={"seat": ["is", "not set"]},
        pluck="name"
    )

    letters = ["A", "B", "C", "D", "E"]

    for ticket in tickets:
        number = random.randint(1, 99)
        letter = random.choice(letters)

        seat = str(number) + letter

        frappe.db.set_value("Airplane Ticket", ticket, "seat", seat)