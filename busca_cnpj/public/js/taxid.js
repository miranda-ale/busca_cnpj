frappe.provide("busca_cnpj.taxid");

// CNPJ pode ser alfanumérico; CPF é só dígitos (11).
busca_cnpj.taxid.strip = function (value) {
	return (value || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 14);
};

// Máscara progressiva: CPF (000.000.000-00) até 11 dígitos; acima disso, ou com letras, CNPJ (00.000.000/0000-00).
busca_cnpj.taxid.mask = function (value) {
	const base = busca_cnpj.taxid.strip(value);
	if (base.length <= 11 && /^\d*$/.test(base)) {
		return base
			.replace(/^(\d{3})(\d)/, "$1.$2")
			.replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
			.replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d)/, "$1.$2.$3-$4");
	}
	return base
		.replace(/^(\w{2})(\w)/, "$1.$2")
		.replace(/^(\w{2})\.(\w{3})(\w)/, "$1.$2.$3")
		.replace(/^(\w{2})\.(\w{3})\.(\w{3})(\w)/, "$1.$2.$3/$4")
		.replace(/^(\w{2})\.(\w{3})\.(\w{3})\/(\w{4})(\w)/, "$1.$2.$3/$4-$5");
};

// Aplica a máscara enquanto o usuário digita e limita o tamanho (CNPJ mascarado = 18 caracteres).
busca_cnpj.taxid.bind_input = function (field) {
	const $input = field && field.$input;
	if (!$input || $input.data("taxid_mask_bound")) return;

	$input.data("taxid_mask_bound", true).attr("maxlength", 18);
	$input.on("input", function () {
		const raw = $(this).val();
		const masked = busca_cnpj.taxid.mask(raw);
		if (raw !== masked) $(this).val(masked);
	});
};
