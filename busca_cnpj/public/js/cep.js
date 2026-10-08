frappe.provide("busca_cnpj.cep");

busca_cnpj.cep.strip = function (value) {
	return (value || "").replace(/\D/g, "").slice(0, 8);
};

busca_cnpj.cep.mask = function (digits) {
	return digits.length > 5 ? digits.slice(0, 5) + "-" + digits.slice(5) : digits;
};

// Mask while typing, Enter triggers `on_search`.
busca_cnpj.cep.bind_input = function (field, on_search) {
	const $input = field && field.$input;
	if (!$input || $input.data("cep_mask_bound")) return;

	$input.data("cep_mask_bound", true);
	$input.on("input", function () {
		const raw = $(this).val();
		const masked = busca_cnpj.cep.mask(busca_cnpj.cep.strip(raw));
		if (raw !== masked) $(this).val(masked);
	});
	$input.on("keydown", function (e) {
		if (e.key === "Enter") {
			e.preventDefault();
			on_search();
		}
	});
};

busca_cnpj.cep.add_button = function (field, on_click) {
	if (!field || !field.$wrapper) return;

	const $control_input = field.$wrapper.find(".control-input");
	if (!$control_input.length || $control_input.find(".btn-busca-cep").length) return;

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
	$btn.on("click", on_click);
};

// Validates the typed CEP and calls ViaCEP; `callback` receives the address dict.
busca_cnpj.cep.lookup = function (value, callback) {
	const digits = busca_cnpj.cep.strip(value);

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
			if (r.message) callback(r.message);
		},
	});
};
