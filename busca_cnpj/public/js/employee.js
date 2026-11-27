frappe.ui.form.on("Employee", {
	refresh(frm) {
		const search = () => buscar_cep_employee(frm);
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

function buscar_cep_employee(frm) {
	busca_cnpj.cep.lookup(frm.doc.custom_current_cep, (d) => {
		const cidade = [d.city, d.state].filter(Boolean).join("/");
		const endereco = [d.address_line1, d.bairro, cidade, "CEP " + d.pincode]
			.filter(Boolean)
			.join(", ");

		const aplicar = () => {
			frm.set_value("custom_current_cep", d.pincode);
			frm.set_value("current_address", endereco);
			frappe.show_alert({
				message: __("Endereço atual preenchido. Complete com número e complemento."),
				indicator: "green",
			});
		};

		if (frm.doc.current_address && frm.doc.current_address !== endereco) {
			frappe.confirm(__("Substituir o Endereço Atual pelo endereço do CEP?"), aplicar);
		} else {
			aplicar();
		}
	});
}
