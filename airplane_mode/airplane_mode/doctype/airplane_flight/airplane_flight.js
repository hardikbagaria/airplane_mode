// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Airplane Flight", {

    setup(frm) {

        // Filter Crew Member field inside the child table
        frm.set_query("crew_member", "crew_members", function () {

            // If Airplane is not selected,
            // don't show any Crew Members
            if (!frm.__flight_airline) {
                return {
                    filters: {
                        name: ["=", ""]
                    }
                };
            }

            // Get already selected Crew Members
            const selected_crew = (frm.doc.crew_members || [])
                .map(row => row.crew_member)
                .filter(Boolean);

            let filters = {
                airline: frm.__flight_airline
            };

            // Remove already selected Crew Members
            if (selected_crew.length) {
                filters.name = ["not in", selected_crew];
            }

            return {
                filters: filters
            };

        });

    },


    async airplane(frm) {

        // Reset stored airline
        frm.__flight_airline = null;


        // If Airplane is cleared
        if (!frm.doc.airplane) {

            frm.clear_table("crew_members");
            frm.refresh_field("crew_members");

            return;
        }


        // Get Airline from Airplane
        const result = await frappe.db.get_value(
            "Airplane",
            frm.doc.airplane,
            "airline"
        );


        if (result.message && result.message.airline) {

            frm.__flight_airline = result.message.airline;

        }


        // Refresh Crew Member dropdown
        frm.refresh_field("crew_members");

    },


    validate: async function(frm) {

        let captain = 0;
        let first_officer = 0;
        let cabin_crew = 0;

        let selected_crew = new Set();


        // Get airline if it hasn't already been fetched
        if (frm.doc.airplane && !frm.__flight_airline) {

            const result = await frappe.db.get_value(
                "Airplane",
                frm.doc.airplane,
                "airline"
            );

            if (result.message) {
                frm.__flight_airline = result.message.airline;
            }
        }


        // Check every crew member
        for (const row of frm.doc.crew_members || []) {

            if (!row.crew_member) {
                continue;
            }


            // ---------------------------------------
            // Prevent duplicate Crew Members
            // ---------------------------------------

            if (selected_crew.has(row.crew_member)) {

                frappe.throw(
                    `Crew Member "${row.crew_member}" has already been selected.`
                );

            }

            selected_crew.add(row.crew_member);


            // ---------------------------------------
            // Fetch Crew Member details
            // ---------------------------------------

            const result = await frappe.db.get_value(
                "Crew Member",
                row.crew_member,
                [
                    "role",
                    "airline"
                ]
            );


            if (!result.message) {
                continue;
            }


            const role = result.message.role;
            const airline = result.message.airline;


            // ---------------------------------------
            // Set Role in child table
            // ---------------------------------------

            await frappe.model.set_value(
                row.doctype,
                row.name,
                "role",
                role
            );


            // ---------------------------------------
            // Check Airline
            // ---------------------------------------

            if (
                frm.__flight_airline &&
                airline !== frm.__flight_airline
            ) {

                frappe.throw(
                    `Crew Member "${row.crew_member}" does not belong to the flight's Airline.`
                );

            }


            // ---------------------------------------
            // Count Roles
            // ---------------------------------------

            if (role === "Captain") {

                captain++;

            }
            else if (role === "First Officer") {

                first_officer++;

            }
            else if (
                role === "Air Hostesses" ||
                role === "Cabin Crew"
            ) {

                cabin_crew++;

            }

        }


        // ---------------------------------------
        // Crew Requirements
        // ---------------------------------------

        if (captain !== 1) {

            frappe.throw(
                "Flight must have exactly 1 Captain."
            );

        }


        if (first_officer !== 1) {

            frappe.throw(
                "Flight must have exactly 1 First Officer."
            );

        }


        if (cabin_crew < 2) {

            frappe.throw(
                "Flight must have at least 2 Air Hostesses or Cabin Crew."
            );

        }

    }

});


// =====================================================
// Flight Crew Member
// =====================================================

frappe.ui.form.on("Flight Crew Member", {

    async crew_member(frm, cdt, cdn) {

        const row = locals[cdt][cdn];


        // If Crew Member is cleared
        if (!row.crew_member) {

            await frappe.model.set_value(
                cdt,
                cdn,
                "role",
                ""
            );

            return;
        }


        // Fetch Role from Crew Member
        const result = await frappe.db.get_value(
            "Crew Member",
            row.crew_member,
            "role"
        );


        if (result.message) {

            await frappe.model.set_value(
                cdt,
                cdn,
                "role",
                result.message.role
            );

        }

    }

});
