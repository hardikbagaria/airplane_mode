// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

// Copyright (c) 2026, Haradik Bagaria - AESPL and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rent Agreement", {
    setup(frm) {
        frm.set_query("airport_shop", () => {
            return {
                filters: {
                    is_rentable: 1
                }
            };
        });
    }
});