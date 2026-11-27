frappe.ui.form.on("Address", {
	refresh(frm) {
		const search = () => buscar_cep_address(frm);
		busca_cnpj.cep.add_button(frm.fields_dict.pincode, search);
		busca_cnpj.cep.bind_input(frm.fields_dict.pincode, search);
	},

	pincode(frm) {
		const raw = frm.doc.pincode || "";
		const digits = busca_cnpj.cep.strip(raw);
		if (digits.length === 8 && raw !== busca_cnpj.cep.mask(digits)) {
			frm.set_value("pincode", busca_cnpj.cep.mask(digits));
		}
	},
});

function buscar_cep_address(frm) {
	busca_cnpj.cep.lookup(frm.doc.pincode, (d) => {
		const values = {
			pincode: d.pincode,
			address_line1: d.address_line1,
			custom_bairro: d.bairro,
			city: d.city,
			state: d.state,
			country: "Brazil",
		};
		// CEPs genéricos (de cidade) vêm sem logradouro/bairro: não apaga o que já foi digitado.
		if (d.address_line2 && !frm.doc.address_line2) values.address_line2 = d.address_line2;
		for (const key of Object.keys(values)) {
			if (values[key]) frm.set_value(key, values[key]);
		}
		frappe.show_alert({ message: __("Endereço preenchido pelo CEP."), indicator: "green" });
	});
}
