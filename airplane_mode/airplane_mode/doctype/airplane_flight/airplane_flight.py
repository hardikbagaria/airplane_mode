# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator


class AirplaneFlight(WebsiteGenerator):

    def validate(self):
        self.validate_crew_members()

    def validate_crew_members(self):

        # No crew members
        if not self.crew_members:
            frappe.throw("Please add Crew Members to the flight.")

        # ---------------------------------------
        # Get Airline from Airplane
        # ---------------------------------------

        if not self.airplane:
            frappe.throw("Please select an Airplane before assigning Crew Members.")

        flight_airline = frappe.db.get_value(
            "Airplane",
            self.airplane,
            "airline"
        )

        if not flight_airline:
            frappe.throw("The selected Airplane does not have an Airline.")

        # ---------------------------------------
        # Counters
        # ---------------------------------------

        captain = 0
        first_officer = 0
        cabin_crew = 0

        selected_crew = set()

        # ---------------------------------------
        # Check every Crew Member
        # ---------------------------------------

        for row in self.crew_members:

            if not row.crew_member:
                frappe.throw("Every Crew Member row must have a Crew Member selected.")

            # ---------------------------------------
            # Prevent duplicates
            # ---------------------------------------

            if row.crew_member in selected_crew:

                frappe.throw(
                    f'Crew Member "{row.crew_member}" has already been assigned to this flight.'
                )

            selected_crew.add(row.crew_member)

            # ---------------------------------------
            # Get Crew Member details
            # ---------------------------------------

            crew_member = frappe.db.get_value(
                "Crew Member",
                row.crew_member,
                ["role", "airline"],
                as_dict=True
            )

            if not crew_member:
                frappe.throw(
                    f'Crew Member "{row.crew_member}" does not exist.'
                )

            role = crew_member.role
            crew_airline = crew_member.airline

            # ---------------------------------------
            # Set Role automatically
            # ---------------------------------------

            row.role = role

            # ---------------------------------------
            # Check Airline
            # ---------------------------------------

            if crew_airline != flight_airline:

                frappe.throw(
                    f'Crew Member "{row.crew_member}" does not belong '
                    f'to the Airline of this flight.'
                )

            # ---------------------------------------
            # Count Roles
            # ---------------------------------------

            if role == "Captain":

                captain += 1

            elif role == "First Officer":

                first_officer += 1

            elif role in ["Air Hostesses", "Cabin Crew"]:

                cabin_crew += 1

        # ---------------------------------------
        # Crew Requirements
        # ---------------------------------------

        if captain != 1:

            frappe.throw(
                "Flight must have exactly 1 Captain."
            )

        if first_officer != 1:

            frappe.throw(
                "Flight must have exactly 1 First Officer."
            )

        if cabin_crew < 2:

            frappe.throw(
                "Flight must have at least 2 Air Hostesses or Cabin Crew."
            )


    def on_submit(self):

        self.status = "Completed"
        self.db_set("status", "Completed")

