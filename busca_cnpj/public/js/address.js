frappe.ui.form.on("Address", {
	refresh(frm) {
		setup_cep_button(frm);
		setup_cep_mask(frm);
	},

	pincode(frm) {
		format_cep_field(frm);
	},
});


// ---------------------------------------------------------------------------
// CEP formatting
// ---------------------------------------------------------------------------

function strip_cep(value) {
	return (value || "").replace(/\D/g, "").slice(0, 8);
}

function mask_cep(digits) {
	return digits.length > 5 ? digits.slice(0, 5) + "-" + digits.slice(5) : digits;
}

function format_cep_field(frm) {
	const raw = frm.doc.pincode || "";
	const digits = strip_cep(raw);
	if (digits.length === 8 && raw !== mask_cep(digits)) {
		frm.set_value("pincode", mask_cep(digits));
	}
}

function setup_cep_mask(frm) {
	const $input = frm.fields_dict.pincode && frm.fields_dict.pincode.$input;
	if (!$input || $input.data("cep_mask_bound")) return;

	$input.data("cep_mask_bound", true);
	$input.on("input", function () {
		const raw = $(this).val();
		const masked = mask_cep(strip_cep(raw));
		if (raw !== masked) {
			$(this).val(masked);
		}
	});
	$input.on("keydown", function (e) {
		if (e.key === "Enter") {
			e.preventDefault();
			buscar_cep(frm);
		}
	});
}


// ---------------------------------------------------------------------------
// Search button next to pincode
// ---------------------------------------------------------------------------

function setup_cep_button(frm) {
	const pincode_field = frm.fields_dict.pincode;
	if (!pincode_field || !pincode_field.$wrapper) return;

	const $control_input = pincode_field.$wrapper.find(".control-input");
	if (!$control_input.length) return;
	if ($control_input.find(".btn-busca-cep").length) return;

	const $btn = $(`
		<span class="btn-busca-cep" style="position:absolute;right:0;top:0;display:flex;align-items:center;height:100%;padding-right:8px;cursor:pointer;z-index:1">
			<button class="btn btn-xs btn-primary" title="${__("Buscar endereço pelo CEP (ViaCEP)")}" style="white-space:nowrap">
				${frappe.utils.icon("search", "xs")}
				${__("Buscar")}
			</button>
		</span>
	`);

	$control_input.css("position", "relative");
	$control_input.find("input").css("padding-right", "90px");
	$control_input.append($btn);

	$btn.on("click", function () {
		buscar_cep(frm);
	});
}


// ---------------------------------------------------------------------------
// CEP search flow
// ---------------------------------------------------------------------------

function buscar_cep(frm) {
	const digits = strip_cep(frm.doc.pincode);

	if (!digits) {
		frappe.msgprint(__("Informe o CEP antes de buscar."));
		return;
	}

	if (digits.length !== 8) {
		frappe.msgprint({
			title: __("CEP Inválido"),
			message: __("O CEP deve ter 8 dígitos."),
			indicator: "red",
		});
		return;
	}

	frappe.call({
		method: "busca_cnpj.api.buscar_cep",
		args: { cep: digits },
		freeze: true,
		freeze_message: __("Consultando CEP..."),
		callback(r) {
			if (!r.message) return;
			const d = r.message;
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
		},
	});
}
