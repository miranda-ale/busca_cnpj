frappe.ui.form.on("Supplier", {
	refresh(frm) {
		setup_cnpj_button(frm);
		setup_cnpj_mask(frm);
	},

	tax_id(frm) {
		format_cnpj_field(frm);
	},

	supplier_name(frm) {
		sanitize_supplier_name(frm);
	},
});


// ---------------------------------------------------------------------------
// CNPJ formatting & validation
// ---------------------------------------------------------------------------

const CNPJ_WEIGHTS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
const CNPJ_WEIGHTS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

function strip_cnpj(value) {
	return (value || "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 14);
}

function format_cnpj(base) {
	if (base.length !== 14) return base;
	return (
		base.slice(0, 2) + "." +
		base.slice(2, 5) + "." +
		base.slice(5, 8) + "/" +
		base.slice(8, 12) + "-" +
		base.slice(12)
	);
}

function validate_cnpj(cnpj) {
	const base = strip_cnpj(cnpj);
	if (base.length !== 14) return false;
	if (!/^[A-Z0-9]{12}\d{2}$/.test(base)) return false;
	if (base === base[0].repeat(14)) return false;

	function calc_digit(chars, weights) {
		let total = 0;
		for (let i = 0; i < weights.length; i++) {
			total += (chars.charCodeAt(i) - 48) * weights[i];
		}
		const remainder = total % 11;
		return remainder < 2 ? 0 : 11 - remainder;
	}

	if (calc_digit(base.slice(0, 12), CNPJ_WEIGHTS_1) !== parseInt(base[12], 10)) return false;
	if (calc_digit(base.slice(0, 13), CNPJ_WEIGHTS_2) !== parseInt(base[13], 10)) return false;
	return true;
}

function format_cnpj_field(frm) {
	const raw = frm.doc.tax_id || "";
	const base = strip_cnpj(raw);
	if (base.length === 14) {
		const formatted = format_cnpj(base);
		if (raw !== formatted) {
			frm.set_value("tax_id", formatted);
		}
	}
}


// ---------------------------------------------------------------------------
// Supplier name sanitization
// ---------------------------------------------------------------------------

function sanitize_supplier_name(frm) {
	const name = frm.doc.supplier_name || "";
	const sanitized = name
		.normalize("NFD")
		.replace(/[\u0300-\u036f]/g, "")
		.toUpperCase()
		.replace(/[^A-Z0-9\s&\-./]/g, "")
		.replace(/\s{2,}/g, " ")
		.trim();

	if (name !== sanitized && sanitized) {
		frm.set_value("supplier_name", sanitized);
	}
}


// ---------------------------------------------------------------------------
// Search button next to tax_id
// ---------------------------------------------------------------------------

function setup_cnpj_button(frm) {
	const tax_id_field = frm.fields_dict.tax_id;
	if (!tax_id_field || !tax_id_field.$wrapper) return;

	const $control_input = tax_id_field.$wrapper.find(".control-input");
	if (!$control_input.length) return;
	if ($control_input.find(".btn-busca-cnpj").length) return;

	const $btn = $(`
		<span class="btn-busca-cnpj" style="position:absolute;right:0;top:0;display:flex;align-items:center;height:100%;padding-right:8px;cursor:pointer;z-index:1">
			<button class="btn btn-xs btn-primary" title="${__("Buscar CNPJ na Receita Federal")}" style="white-space:nowrap">
				${frappe.utils.icon("search", "xs")}
				${__("Buscar")}
			</button>
		</span>
	`);

	$control_input.css("position", "relative");
	$control_input.find("input").css("padding-right", "90px");
	$control_input.append($btn);

	$btn.on("click", function () {
		buscar_cnpj(frm);
	});
}


// ---------------------------------------------------------------------------
// Real-time CNPJ mask on input
// ---------------------------------------------------------------------------

function setup_cnpj_mask(frm) {
	const $input = frm.fields_dict.tax_id && frm.fields_dict.tax_id.$input;
	if (!$input || $input.data("cnpj_mask_bound")) return;

	$input.data("cnpj_mask_bound", true);
	$input.on("input", function () {
		const raw = $(this).val();
		const base = strip_cnpj(raw);
		let masked = base;
		if (base.length > 2) masked = base.slice(0, 2) + "." + base.slice(2);
		if (base.length > 5) masked = masked.slice(0, 6) + "." + base.slice(5);
		if (base.length > 8) masked = masked.slice(0, 10) + "/" + base.slice(8);
		if (base.length > 12) masked = masked.slice(0, 15) + "-" + base.slice(12);
		if (raw !== masked) {
			$(this).val(masked);
		}
	});
}


// ---------------------------------------------------------------------------
// CNPJ search flow
// ---------------------------------------------------------------------------

function buscar_cnpj(frm) {
	const cnpj = frm.doc.tax_id || "";
	const base = strip_cnpj(cnpj);

	if (!base) {
		frappe.msgprint(__("Informe o CNPJ antes de buscar."));
		return;
	}

	if (!validate_cnpj(base)) {
		frappe.msgprint({
			title: __("CNPJ Inválido"),
			message: __("O CNPJ informado não é válido. Verifique os dígitos."),
			indicator: "red",
		});
		return;
	}

	frappe.call({
		method: "busca_cnpj.api.buscar_cnpj",
		args: { cnpj: base },
		freeze: true,
		freeze_message: __("Consultando CNPJ na Receita Federal..."),
		callback(r) {
			if (r.message) {
				show_cnpj_modal(frm, r.message);
			}
		},
	});
}


// ---------------------------------------------------------------------------
// Confirmation modal
// ---------------------------------------------------------------------------

function show_cnpj_modal(frm, dados) {
	const situacao_class = dados.situacao_ativa ? "green" : "red";
	const situacao_label = dados.situacao_cadastral || "N/A";

	let socios_html = "";
	if (dados.socios && dados.socios.length) {
		socios_html = dados.socios
			.map(
				(s) =>
					`<tr>
						<td style="padding:4px 8px">${frappe.utils.escape_html(s.nome)}</td>
						<td style="padding:4px 8px">${frappe.utils.escape_html(s.qualificacao)}</td>
					</tr>`
			)
			.join("");
		socios_html = `
			<h5 style="margin-top:15px">${__("Quadro Societário (QSA)")}</h5>
			<table class="table table-bordered table-sm" style="font-size:12px">
				<thead><tr>
					<th style="padding:4px 8px">${__("Nome")}</th>
					<th style="padding:4px 8px">${__("Qualificação")}</th>
				</tr></thead>
				<tbody>${socios_html}</tbody>
			</table>
		`;
	}

	let cnaes_html = "";
	if (dados.cnaes && dados.cnaes.length) {
		cnaes_html = dados.cnaes
			.map(
				(c) =>
					`<tr>
						<td style="padding:4px 8px">${frappe.utils.escape_html(c.cnae_code)}</td>
						<td style="padding:4px 8px">${frappe.utils.escape_html(c.description)}</td>
						<td style="padding:4px 8px;text-align:center">${c.is_primary ? "✔" : ""}</td>
					</tr>`
			)
			.join("");
		cnaes_html = `
			<h5 style="margin-top:15px">${__("CNAEs")}</h5>
			<table class="table table-bordered table-sm" style="font-size:12px">
				<thead><tr>
					<th style="padding:4px 8px">${__("Código")}</th>
					<th style="padding:4px 8px">${__("Descrição")}</th>
					<th style="padding:4px 8px;text-align:center">${__("Principal")}</th>
				</tr></thead>
				<tbody>${cnaes_html}</tbody>
			</table>
		`;
	}

	const end = dados.endereco || {};
	const endereco_parts = [
		end.address_line1,
		end.address_line2,
		[end.city, end.state].filter(Boolean).join("/"),
		end.pincode ? "CEP " + end.pincode : "",
	].filter(Boolean);

	const html = `
		<div style="font-size:13px">
			<div class="row" style="margin-bottom:10px">
				<div class="col-sm-8">
					<strong>${__("Razão Social")}</strong><br>
					${frappe.utils.escape_html(dados.razao_social)}
				</div>
				<div class="col-sm-4 text-right">
					<span class="indicator-pill ${situacao_class}">
						${frappe.utils.escape_html(situacao_label)}
					</span>
				</div>
			</div>

			${dados.nome_fantasia ? `
			<div style="margin-bottom:8px">
				<strong>${__("Nome Fantasia")}</strong><br>
				${frappe.utils.escape_html(dados.nome_fantasia)}
			</div>` : ""}

			<div class="row" style="margin-bottom:8px">
				<div class="col-sm-6">
					<strong>${__("CNPJ")}</strong><br>
					${frappe.utils.escape_html(dados.cnpj_formatado)}
				</div>
				<div class="col-sm-6">
					<strong>${__("Natureza Jurídica")}</strong><br>
					${frappe.utils.escape_html(dados.natureza_juridica || "N/A")}
				</div>
			</div>

			<div style="margin-bottom:8px">
				<strong>${__("Endereço")}</strong><br>
				${frappe.utils.escape_html(endereco_parts.join(" - "))}
			</div>

			<div class="row" style="margin-bottom:8px">
				<div class="col-sm-6">
					<strong>${__("Telefone")}</strong><br>
					${frappe.utils.escape_html(dados.telefone_1 || "N/A")}
				</div>
				<div class="col-sm-6">
					<strong>${__("E-mail")}</strong><br>
					${frappe.utils.escape_html(dados.email || "N/A")}
				</div>
			</div>

			${cnaes_html}
			${socios_html}

			${!dados.situacao_ativa ? `
			<div class="alert alert-warning" style="margin-top:10px">
				<strong>${__("Atenção")}:</strong>
				${__("Esta empresa não está com situação cadastral ATIVA na Receita Federal.")}
			</div>` : ""}
		</div>
	`;

	const dialog = new frappe.ui.Dialog({
		title: __("Dados do CNPJ - Confirmar Preenchimento"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "cnpj_preview",
				options: html,
			},
		],
		primary_action_label: __("Confirmar e Preencher"),
		primary_action() {
			dialog.hide();
			aplicar_dados_cnpj(frm, dados);
		},
		secondary_action_label: __("Cancelar"),
	});

	dialog.show();
}


// ---------------------------------------------------------------------------
// Apply confirmed data
// ---------------------------------------------------------------------------

function aplicar_dados_cnpj(frm, dados) {
	if (frm.is_new()) {
		frm.set_value("tax_id", dados.cnpj_formatado);
		frm.set_value("supplier_name", dados.razao_social);
		frm.set_value("supplier_type", "Company");

		frappe.show_alert({
			message: __("Salvando fornecedor..."),
			indicator: "blue",
		}, 3);

		frm.save().then(() => {
			_chamar_confirmar(frm, dados);
		}).catch((err) => {
			frappe.msgprint({
				title: __("Erro ao salvar fornecedor"),
				message: __("Não foi possível salvar o fornecedor. Verifique se o CNPJ já está cadastrado."),
				indicator: "red",
			});
			console.error("Busca CNPJ - erro ao salvar:", err);
		});
		return;
	}

	_chamar_confirmar(frm, dados);
}

function _chamar_confirmar(frm, dados) {
	frappe.call({
		method: "busca_cnpj.api.confirmar_dados_cnpj",
		args: {
			supplier_name: frm.doc.name,
			dados: JSON.stringify(dados),
		},
		freeze: true,
		freeze_message: __("Preenchendo dados do fornecedor..."),
		callback(r) {
			if (!r.message) return;

			const res = r.message;
			const parts = [];
			if (res.address) parts.push(__("Endereço"));
			if (res.contact) parts.push(__("Contato"));
			if (res.cnaes_count) parts.push(__("{0} CNAEs", [res.cnaes_count]));

			const warnings = [];
			if (!res.address) warnings.push(__("Endereço não criado (dados insuficientes da Receita Federal)."));
			if (!res.contact) warnings.push(__("Contato não criado (sem sócios, telefone ou e-mail)."));

			if (parts.length) {
				frappe.show_alert({
					message: __("Fornecedor atualizado! Vinculados: {0}.", [parts.join(", ")]),
					indicator: "green",
				}, 7);
			}

			if (warnings.length) {
				frappe.msgprint({
					title: __("Aviso"),
					message: warnings.join("<br>"),
					indicator: "orange",
				});
			}

			if (res.supplier !== frm.doc.name) {
				frappe.set_route("Form", "Supplier", res.supplier);
			} else {
				frm.reload_doc();
			}
		},
		error(err) {
			frappe.msgprint({
				title: __("Erro ao confirmar dados"),
				message: __("Ocorreu um erro ao preencher os dados do fornecedor. Verifique o Error Log."),
				indicator: "red",
			});
			console.error("Busca CNPJ - erro em confirmar_dados_cnpj:", err);
		},
	});
}
