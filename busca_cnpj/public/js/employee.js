frappe.ui.form.on("Employee", {
	refresh(frm) {
		const search = () => lookup_cep_employee(frm);
		busca_cnpj.cep.add_button(frm.fields_dict.custom_current_cep, search);
		busca_cnpj.cep.bind_input(frm.fields_dict.custom_current_cep, search);
	},

	custom_current_cep(frm) {
		const raw = frm.doc.custom_current_cep || "";
		const digits = busca_cnpj.cep.strip(raw);
		if (digits.length === 8 && raw !== busca_cnpj.cep.mask(digits)) {
			frm.set_value("custom_current_cep", busca_cnpj.cep.mask(digits));
		}
	},
});

function lookup_cep_employee(frm) {
	busca_cnpj.cep.lookup(frm.doc.custom_current_cep, (d) => {
		const city_state = [d.city, d.state].filter(Boolean).join("/");
		const address_text = [d.address_line1, d.bairro, city_state, "CEP " + d.pincode]
			.filter(Boolean)
			.join(", ");

		const apply_address = () => {
			frm.set_value("custom_current_cep", d.pincode);
			frm.set_value("current_address", address_text);
			frappe.show_alert({
				message: __("Endereço atual preenchido. Complete com número e complemento."),
				indicator: "green",
			});
		};

		if (frm.doc.current_address && frm.doc.current_address !== address_text) {
			frappe.confirm(__("Substituir o Endereço Atual pelo endereço do CEP?"), apply_address);
		} else {
			apply_address();
		}
	});
}
