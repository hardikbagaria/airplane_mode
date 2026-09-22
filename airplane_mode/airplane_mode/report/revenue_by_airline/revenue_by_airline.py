import frappe
from frappe.query_builder import DocType
from pypika.functions import Sum


def execute(filters=None):
    Airline = DocType("Airline")
    Airplane = DocType("Airplane")
    Flight = DocType("Airplane Flight")
    Ticket = DocType("Airplane Ticket")

    data = (
        frappe.qb.from_(Airline)
        .left_join(Airplane)
        .on(Airplane.airline == Airline.name)
        .left_join(Flight)
        .on(Flight.airplane == Airplane.name)
        .left_join(Ticket)
        .on(
            (Ticket.flight == Flight.name)
            & (Ticket.docstatus == 1)
        )
        .select(
            Airline.name.as_("airline"),
            Sum(Ticket.total_amount).as_("revenue")
        )
        .groupby(Airline.name)
        .orderby(Sum(Ticket.total_amount), order=frappe.qb.desc)
        .run(as_dict=True)
    )

    for row in data:
        row.revenue = row.revenue or 0

    columns = [
        {
            "label": "Airline",
            "fieldname": "airline",
            "fieldtype": "Link",
            "options": "Airline"
        },
        {
            "label": "Revenue",
            "fieldname": "revenue",
            "fieldtype": "Currency"
        }
    ]

    total_revenue = sum(row.revenue for row in data)

    chart = {
        "data": {
            "labels": [row.airline for row in data],
            "datasets": [
                {
                    "name": "Revenue",
                    "values": [row.revenue for row in data]
                }
            ]
        },
        "type": "donut"
    }
    report_summary = [
        {
            "indicator": "Green",
			"label": "Total Revenue",
			"value": total_revenue,
			"datatype": "Currency",
		}
	]

    return columns, data, None, chart, report_summary