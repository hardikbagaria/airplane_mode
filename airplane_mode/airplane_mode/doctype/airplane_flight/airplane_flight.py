# Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
# For license information, please see license.txt

import frappe
from frappe.website.website_generator import WebsiteGenerator


class AirplaneFlight(WebsiteGenerator):

    def before_submit(self):
        self.status = "Completed"

    def get_context(self, context):
        context.flight = self
        context.title = self.flight_number