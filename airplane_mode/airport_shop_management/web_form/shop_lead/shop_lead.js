frappe.ready(function() {
	frappe.web_form.after_load = () => {
		const params = new URLSearchParams(window.location.search);
		const shop = params.get("shop") || params.get("airport_shop");
		if (shop) {
			frappe.web_form.set_value("shop", shop);
			frappe.web_form.set_df_property("shop", "read_only", 1);
		}
	};
});
