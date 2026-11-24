import json
import re
import unicodedata

import frappe
import requests
from frappe import _

from busca_cnpj.cnpj import format_cnpj, normalize_cnpj, validate_cnpj

BRASILAPI_BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"
MINHA_RECEITA_BASE_URL = "https://minhareceita.org"
CNPJWS_BASE_URL = "https://publica.cnpj.ws/cnpj"
VIACEP_BASE_URL = "https://viacep.com.br/ws"
SAVEPOINT_RENAME_SUPPLIER = "busca_cnpj_renomear_supplier"


def format_cep(cep: str) -> str:
	digits = re.sub(r"\D", "", str(cep))
	if len(digits) != 8:
		return cep
	return f"{digits[:5]}-{digits[5:]}"


def format_phone(phone: str) -> str:
	digits = re.sub(r"\D", "", str(phone))
	if not digits:
		return ""
	if len(digits) == 11:
		return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
	if len(digits) == 10:
		return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
	return phone


def sanitize_company_name(name: str) -> str:
	if not name:
		return ""
	nfkd = unicodedata.normalize("NFKD", name)
	ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
	upper = ascii_only.upper()
	cleaned = re.sub(r"[^A-Z0-9\s&\-./]", "", upper)
	return re.sub(r"\s{2,}", " ", cleaned).strip()


def _build_address_line1(data: dict) -> str:
	street_type = (data.get("descricao_tipo_de_logradouro") or "").strip()
	street = (data.get("logradouro") or "").strip()
	if street_type and street:
		return f"{street_type} {street}"
	return street or street_type or ""


def _build_address_line2(data: dict) -> str:
	parts = []
	number = (data.get("numero") or "").strip()
	if number:
		parts.append(number)
	complement = (data.get("complemento") or "").strip()
	if complement:
		parts.append(complement)
	return ", ".join(parts)


def _extract_cnaes(data: dict) -> list[dict]:
	cnaes = []
	primary_cnae = data.get("cnae_fiscal")
	if primary_cnae:
		cnaes.append(
			{
				"cnae_code": str(primary_cnae),
				"description": data.get("cnae_fiscal_descricao", ""),
				"is_primary": 1,
			}
		)
	for c in data.get("cnaes_secundarios") or []:
		cnaes.append(
			{
				"cnae_code": str(c.get("codigo", "")),
				"description": c.get("descricao", ""),
				"is_primary": 0,
			}
		)
	return cnaes


def _normalize_cnpjws(d: dict) -> dict:
	"""Convert a CNPJ.ws response to the BrasilAPI format used by lookup_cnpj."""
	establishment = d.get("estabelecimento") or {}
	primary = establishment.get("atividade_principal") or {}
	ddd1, tel1 = establishment.get("ddd1") or "", establishment.get("telefone1") or ""
	ddd2, tel2 = establishment.get("ddd2") or "", establishment.get("telefone2") or ""
	return {
		"razao_social": d.get("razao_social") or "",
		"nome_fantasia": establishment.get("nome_fantasia") or "",
		"situacao_cadastral": establishment.get("situacao_cadastral") or "",
		"natureza_juridica": (d.get("natureza_juridica") or {}).get("descricao", ""),
		"data_inicio_atividade": establishment.get("data_inicio_atividade") or "",
		"cnae_fiscal": primary.get("id") or "",
		"cnae_fiscal_descricao": primary.get("descricao") or "",
		"cnaes_secundarios": [
			{"codigo": a.get("id", ""), "descricao": a.get("descricao", "")}
			for a in establishment.get("atividades_secundarias") or []
		],
		"qsa": [
			{
				"nome_socio": s.get("nome") or "",
				"qualificacao_socio": (s.get("qualificacao_socio") or {}).get("descricao", "").strip(),
			}
			for s in d.get("socios") or []
		],
		"descricao_tipo_de_logradouro": establishment.get("tipo_logradouro") or "",
		"logradouro": establishment.get("logradouro") or "",
		"numero": establishment.get("numero") or "",
		"complemento": establishment.get("complemento") or "",
		"bairro": establishment.get("bairro") or "",
		"municipio": (establishment.get("cidade") or {}).get("nome", ""),
		"uf": (establishment.get("estado") or {}).get("sigla", ""),
		"cep": establishment.get("cep") or "",
		"ddd_telefone_1": f"{ddd1}{tel1}" if tel1 else "",
		"ddd_telefone_2": f"{ddd2}{tel2}" if tel2 else "",
		"email": establishment.get("email") or "",
	}


def _query_api(cnpj: str):
	"""Query CNPJ.ws and, on failure, BrasilAPI and Minha Receita (better alphanumeric CNPJ support)."""
	sources = (
		(f"{CNPJWS_BASE_URL}/{cnpj}", _normalize_cnpjws),
		(f"{BRASILAPI_BASE_URL}/{cnpj}", None),
		(f"{MINHA_RECEITA_BASE_URL}/{cnpj}", None),
	)
	server_error = None
	connected = False

	for url, converter in sources:
		try:
			response = requests.get(url, timeout=15)
		except requests.exceptions.RequestException:
			continue
		connected = True
		if response.status_code == 200:
			try:
				data = response.json()
				return converter(data) if converter else data
			except ValueError:
				server_error = response.status_code
				continue
		if response.status_code not in (400, 404):
			server_error = response.status_code

	if not connected:
		frappe.throw(_("Não foi possível conectar à API de consulta. Tente novamente."))
	if server_error:
		frappe.throw(_("Erro ao consultar CNPJ (código {0}). Tente novamente.").format(server_error))
	frappe.throw(_("CNPJ não encontrado na base da Receita Federal."))


@frappe.whitelist()
def lookup_cnpj(cnpj: str) -> dict:
	base = normalize_cnpj(cnpj)

	if not validate_cnpj(base):
		frappe.throw(_("CNPJ inválido. Verifique os dígitos informados."))

	data = _query_api(base)

	legal_name = sanitize_company_name(data.get("razao_social", ""))
	trade_name = sanitize_company_name(data.get("nome_fantasia", ""))

	partners = []
	for s in data.get("qsa") or []:
		partners.append(
			{
				"nome": s.get("nome_socio") or s.get("nome") or "",
				"qualificacao": s.get("qualificacao_socio") or s.get("qualificacao") or "",
			}
		)

	status = data.get("situacao_cadastral")
	is_active = status == 2 or str(status).upper() == "ATIVA"
	status_description = (
		data.get("descricao_situacao_cadastral")
		or data.get("descricao_situacao")
		or ("" if status in (None, 2) else str(status))
	)
	if is_active and not status_description:
		status_description = "ATIVA"

	return {
		"cnpj_formatado": format_cnpj(base),
		"razao_social": legal_name,
		"nome_fantasia": trade_name,
		"situacao_cadastral": status_description,
		"situacao_ativa": is_active,
		"natureza_juridica": data.get("natureza_juridica", ""),
		"data_inicio_atividade": data.get("data_inicio_atividade", ""),
		"cnae_fiscal": data.get("cnae_fiscal", ""),
		"cnae_fiscal_descricao": data.get("cnae_fiscal_descricao", ""),
		"cnaes": _extract_cnaes(data),
		"endereco": {
			"address_line1": _build_address_line1(data),
			"address_line2": _build_address_line2(data),
			"bairro": (data.get("bairro") or "").strip(),
			"city": data.get("municipio", ""),
			"state": data.get("uf", ""),
			"pincode": format_cep(data.get("cep", "")),
			"phone": format_phone(data.get("ddd_telefone_1", "")),
			"email_id": data.get("email") or "",
		},
		"socios": partners,
		"telefone_1": format_phone(data.get("ddd_telefone_1", "")),
		"telefone_2": format_phone(data.get("ddd_telefone_2", "")),
		"email": data.get("email") or "",
	}


@frappe.whitelist()
def lookup_cep(cep: str) -> dict:
	digits = re.sub(r"\D", "", cep or "")
	if len(digits) != 8:
		frappe.throw(_("CEP inválido. Informe os 8 dígitos."))

	try:
		response = requests.get(f"{VIACEP_BASE_URL}/{digits}/json/", timeout=15)
	except requests.exceptions.RequestException:
		frappe.throw(_("Não foi possível conectar ao ViaCEP. Tente novamente."))

	if response.status_code == 400:
		frappe.throw(_("CEP inválido. Verifique os dígitos informados."))
	if response.status_code != 200:
		frappe.throw(_("Erro ao consultar CEP (código {0}). Tente novamente.").format(response.status_code))

	try:
		data = response.json()
	except ValueError:
		frappe.throw(_("Resposta inválida do ViaCEP. Tente novamente."))

	if data.get("erro"):
		frappe.throw(_("CEP não encontrado."))

	return {
		"pincode": format_cep(digits),
		"address_line1": (data.get("logradouro") or "").strip(),
		"address_line2": (data.get("complemento") or "").strip(),
		"bairro": (data.get("bairro") or "").strip(),
		"city": (data.get("localidade") or "").strip(),
		"state": (data.get("uf") or "").strip(),
	}


@frappe.whitelist(methods=["POST"])
def confirm_cnpj_data(supplier_name: str, data: str) -> dict:
	if isinstance(data, str):
		data = json.loads(data)

	supplier = frappe.get_doc("Supplier", supplier_name)
	new_legal_name = data.get("razao_social", "")
	old_name = supplier.name

	supplier.tax_id = data.get("cnpj_formatado", "")
	supplier.supplier_type = "Company"

	_update_cnaes(supplier, data.get("cnaes", []))

	naming_by_name = frappe.defaults.get_global_default("supp_master_name") == "Supplier Name"

	if naming_by_name and new_legal_name and new_legal_name != old_name:
		supplier.supplier_name = old_name
		supplier.save(ignore_permissions=True)
		# Savepoint instead of a manual commit: if the rename fails, only it is undone and the save above stays in
		# the request transaction (committed at the end of the request).
		frappe.db.savepoint(SAVEPOINT_RENAME_SUPPLIER)
		try:
			frappe.rename_doc("Supplier", old_name, new_legal_name, merge=False)
		except frappe.DuplicateEntryError:
			frappe.db.rollback(save_point=SAVEPOINT_RENAME_SUPPLIER)
			frappe.log_error(
				title="Busca CNPJ: rename falhou",
				message=f"Supplier '{new_legal_name}' já existe. Mantendo nome original.",
			)
		except Exception:
			# Any other error (e.g. ValidationError) is not swallowed: undo the partial rename and propagate.
			frappe.db.rollback(save_point=SAVEPOINT_RENAME_SUPPLIER)
			raise
		supplier = frappe.get_doc("Supplier", frappe.db.exists("Supplier", new_legal_name) or old_name)
	else:
		if new_legal_name:
			supplier.supplier_name = new_legal_name
		supplier.save(ignore_permissions=True)

	address_name = None
	try:
		address_name = _create_address(supplier.name, data)
	except Exception:
		frappe.log_error(
			title="Busca CNPJ: erro ao criar endereço",
			message=f"Supplier: {supplier.name}\n{frappe.get_traceback()}",
		)

	contact_name = None
	try:
		contact_name = _create_contact(supplier.name, data)
	except Exception:
		frappe.log_error(
			title="Busca CNPJ: erro ao criar contato",
			message=f"Supplier: {supplier.name}\n{frappe.get_traceback()}",
		)

	if address_name:
		supplier.reload()
		supplier.supplier_primary_address = address_name
		supplier.save(ignore_permissions=True)

	if contact_name:
		supplier.reload()
		supplier.supplier_primary_contact = contact_name
		supplier.save(ignore_permissions=True)

	cnaes_count = len(data.get("cnaes", []))

	return {
		"supplier": supplier.name,
		"address": address_name,
		"contact": contact_name,
		"cnaes_count": cnaes_count,
	}


def _update_cnaes(supplier, cnaes: list[dict]):
	supplier.set("cnaes", [])
	for cnae in cnaes:
		supplier.append(
			"cnaes",
			{
				"cnae_code": cnae.get("cnae_code", ""),
				"description": cnae.get("description", ""),
				"is_primary": cnae.get("is_primary", 0),
			},
		)


def _create_address(supplier_name: str, data: dict) -> str | None:
	address_data = data.get("endereco", {})
	address_line1 = address_data.get("address_line1", "")
	city = address_data.get("city", "")

	if not address_line1:
		address_line1 = address_data.get("address_line2", "") or "Endereço não informado"

	if not city:
		city = address_data.get("state", "") or "Não informado"

	existing = frappe.db.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Supplier",
			"link_name": supplier_name,
			"parenttype": "Address",
		},
		fields=["parent"],
		limit=1,
	)
	if existing:
		address = frappe.get_doc("Address", existing[0].parent)
	else:
		address = frappe.new_doc("Address")
		address.append("links", {"link_doctype": "Supplier", "link_name": supplier_name})

	address.address_title = supplier_name
	address.address_type = "Office"
	address.address_line1 = address_line1
	address.address_line2 = address_data.get("address_line2", "")
	address.custom_bairro = address_data.get("bairro", "")
	address.city = city
	address.state = address_data.get("state", "")
	address.country = "Brazil"
	address.pincode = address_data.get("pincode", "")
	address.phone = address_data.get("phone", "")
	address.email_id = address_data.get("email_id", "")
	address.is_primary_address = 1
	address.is_shipping_address = 0
	address.save(ignore_permissions=True)
	return address.name


def _create_contact(supplier_name: str, data: dict) -> str | None:
	partners = data.get("socios", [])
	phone = data.get("telefone_1", "")
	email = data.get("email", "")

	if not partners and not phone and not email:
		return None

	existing = frappe.db.get_all(
		"Dynamic Link",
		filters={
			"link_doctype": "Supplier",
			"link_name": supplier_name,
			"parenttype": "Contact",
		},
		fields=["parent"],
		limit=1,
	)
	if existing:
		contact = frappe.get_doc("Contact", existing[0].parent)
		contact.phone_nos = []
		contact.email_ids = []
	else:
		contact = frappe.new_doc("Contact")
		contact.append("links", {"link_doctype": "Supplier", "link_name": supplier_name})

	if partners:
		full_name = partners[0].get("nome", "")
		name_parts = full_name.strip().split()
		if name_parts:
			contact.first_name = name_parts[0]
			if len(name_parts) > 1:
				contact.last_name = " ".join(name_parts[1:])
		contact.designation = partners[0].get("qualificacao", "")
	else:
		contact.first_name = supplier_name

	contact.status = "Passive"
	contact.is_primary_contact = 1

	if phone:
		contact.append("phone_nos", {"phone": phone, "is_primary_phone": 1})

	if email:
		contact.append("email_ids", {"email_id": email, "is_primary": 1})

	contact.save(ignore_permissions=True)
	return contact.name


# Deprecated Portuguese aliases kept for external consumers (integracoes_customizadas imports
# `buscar_cnpj` and `confirmar_dados_cnpj`; the JS of other apps may call them by dotted path).
# Remove once the consumers migrate to `lookup_cnpj` and `confirm_cnpj_data`.
@frappe.whitelist()
def buscar_cep(cep: str) -> dict:
	"""Deprecated alias of `lookup_cep`; remove after external callers migrate."""
	return lookup_cep(cep)


@frappe.whitelist()
def buscar_cnpj(cnpj: str) -> dict:
	return lookup_cnpj(cnpj)


@frappe.whitelist(methods=["POST"])
def confirmar_dados_cnpj(supplier_name: str, dados: str) -> dict:
	return confirm_cnpj_data(supplier_name, dados)


# Deprecated aliases of the formatting helpers; remove after external callers migrate.
formatar_cep = format_cep
formatar_telefone = format_phone
sanitizar_razao_social = sanitize_company_name
SAVEPOINT_RENOMEAR_SUPPLIER = SAVEPOINT_RENAME_SUPPLIER
