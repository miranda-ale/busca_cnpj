import json
import re
import unicodedata

import requests

import frappe
from frappe import _


from busca_cnpj.cnpj import formatar_cnpj, normalizar_cnpj, validar_cnpj

BRASILAPI_BASE_URL = "https://brasilapi.com.br/api/cnpj/v1"
MINHA_RECEITA_BASE_URL = "https://minhareceita.org"


def formatar_cep(cep: str) -> str:
    digits = re.sub(r"\D", "", str(cep))
    if len(digits) != 8:
        return cep
    return f"{digits[:5]}-{digits[5:]}"


def formatar_telefone(tel: str) -> str:
    digits = re.sub(r"\D", "", str(tel))
    if not digits:
        return ""
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return tel


def sanitizar_razao_social(nome: str) -> str:
    if not nome:
        return ""
    nfkd = unicodedata.normalize("NFKD", nome)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    upper = ascii_only.upper()
    cleaned = re.sub(r"[^A-Z0-9\s&\-./]", "", upper)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _montar_address_line1(dados: dict) -> str:
    tipo = (dados.get("descricao_tipo_de_logradouro") or "").strip()
    logradouro = (dados.get("logradouro") or "").strip()
    if tipo and logradouro:
        return f"{tipo} {logradouro}"
    return logradouro or tipo or ""


def _montar_address_line2(dados: dict) -> str:
    parts = []
    numero = (dados.get("numero") or "").strip()
    if numero:
        parts.append(numero)
    complemento = (dados.get("complemento") or "").strip()
    if complemento:
        parts.append(complemento)
    bairro = (dados.get("bairro") or "").strip()
    if bairro:
        parts.append(f"Bairro {bairro}")
    return ", ".join(parts)


def _extrair_cnaes(dados: dict) -> list[dict]:
    cnaes = []
    cnae_principal = dados.get("cnae_fiscal")
    if cnae_principal:
        cnaes.append({
            "cnae_code": str(cnae_principal),
            "description": dados.get("cnae_fiscal_descricao", ""),
            "is_primary": 1,
        })
    for c in dados.get("cnaes_secundarios") or []:
        cnaes.append({
            "cnae_code": str(c.get("codigo", "")),
            "description": c.get("descricao", ""),
            "is_primary": 0,
        })
    return cnaes


def _consultar_api(cnpj: str):
	"""Consulta BrasilAPI e, se não achar, Minha Receita (melhor suporte alfanumérico)."""
	urls = (
		f"{BRASILAPI_BASE_URL}/{cnpj}",
		f"{MINHA_RECEITA_BASE_URL}/{cnpj}",
	)
	ultimo_status = None
	conectou = False

	for url in urls:
		try:
			response = requests.get(url, timeout=15)
		except requests.exceptions.RequestException:
			continue
		conectou = True
		ultimo_status = response.status_code
		if response.status_code == 200:
			return response.json()
		if response.status_code not in (400, 404):
			frappe.throw(
				_("Erro ao consultar CNPJ (código {0}). Tente novamente.").format(
					response.status_code
				)
			)

	if not conectou:
		frappe.throw(_("Não foi possível conectar à API de consulta. Tente novamente."))
	if ultimo_status == 404:
		frappe.throw(_("CNPJ não encontrado na base da Receita Federal."))
	frappe.throw(_("CNPJ não encontrado na base da Receita Federal."))


@frappe.whitelist()
def buscar_cnpj(cnpj: str) -> dict:
    base = normalizar_cnpj(cnpj)

    if not validar_cnpj(base):
        frappe.throw(_("CNPJ inválido. Verifique os dígitos informados."))

    dados = _consultar_api(base)

    razao = sanitizar_razao_social(dados.get("razao_social", ""))
    fantasia = sanitizar_razao_social(dados.get("nome_fantasia", ""))

    socios = []
    for s in dados.get("qsa") or []:
        socios.append({
            "nome": s.get("nome_socio") or s.get("nome") or "",
            "qualificacao": s.get("qualificacao_socio") or s.get("qualificacao") or "",
        })

    situacao = dados.get("situacao_cadastral")
    situacao_ativa = situacao == 2 or str(situacao).upper() == "ATIVA"
    situacao_desc = (
        dados.get("descricao_situacao_cadastral")
        or dados.get("descricao_situacao")
        or ("" if situacao in (None, 2) else str(situacao))
    )
    if situacao_ativa and not situacao_desc:
        situacao_desc = "ATIVA"

    return {
        "cnpj_formatado": formatar_cnpj(base),
        "razao_social": razao,
        "nome_fantasia": fantasia,
        "situacao_cadastral": situacao_desc,
        "situacao_ativa": situacao_ativa,
        "natureza_juridica": dados.get("natureza_juridica", ""),
        "data_inicio_atividade": dados.get("data_inicio_atividade", ""),
        "cnae_fiscal": dados.get("cnae_fiscal", ""),
        "cnae_fiscal_descricao": dados.get("cnae_fiscal_descricao", ""),
        "cnaes": _extrair_cnaes(dados),
        "endereco": {
            "address_line1": _montar_address_line1(dados),
            "address_line2": _montar_address_line2(dados),
            "city": dados.get("municipio", ""),
            "state": dados.get("uf", ""),
            "pincode": formatar_cep(dados.get("cep", "")),
            "phone": formatar_telefone(dados.get("ddd_telefone_1", "")),
            "email_id": dados.get("email") or "",
        },
        "socios": socios,
        "telefone_1": formatar_telefone(dados.get("ddd_telefone_1", "")),
        "telefone_2": formatar_telefone(dados.get("ddd_telefone_2", "")),
        "email": dados.get("email") or "",
    }


@frappe.whitelist()
def confirmar_dados_cnpj(supplier_name: str, dados: str) -> dict:
    if isinstance(dados, str):
        dados = json.loads(dados)

    supplier = frappe.get_doc("Supplier", supplier_name)
    new_razao = dados.get("razao_social", "")
    old_name = supplier.name

    supplier.tax_id = dados.get("cnpj_formatado", "")
    supplier.supplier_type = "Company"

    _atualizar_cnaes(supplier, dados.get("cnaes", []))

    naming_by_name = (
        frappe.defaults.get_global_default("supp_master_name") == "Supplier Name"
    )

    if naming_by_name and new_razao and new_razao != old_name:
        supplier.supplier_name = old_name
        supplier.save(ignore_permissions=True)
        frappe.db.commit()
        try:
            frappe.rename_doc("Supplier", old_name, new_razao, merge=False)
        except frappe.DuplicateEntryError:
            frappe.log_error(
                title="Busca CNPJ: rename falhou",
                message=f"Supplier '{new_razao}' já existe. Mantendo nome original.",
            )
        supplier = frappe.get_doc("Supplier", frappe.db.exists("Supplier", new_razao) or old_name)
    else:
        if new_razao:
            supplier.supplier_name = new_razao
        supplier.save(ignore_permissions=True)

    address_name = None
    try:
        address_name = _criar_endereco(supplier.name, dados)
    except Exception:
        frappe.log_error(
            title="Busca CNPJ: erro ao criar endereço",
            message=f"Supplier: {supplier.name}\n{frappe.get_traceback()}",
        )

    contact_name = None
    try:
        contact_name = _criar_contato(supplier.name, dados)
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

    cnaes_count = len(dados.get("cnaes", []))

    return {
        "supplier": supplier.name,
        "address": address_name,
        "contact": contact_name,
        "cnaes_count": cnaes_count,
    }


def _atualizar_cnaes(supplier, cnaes: list[dict]):
    supplier.set("cnaes", [])
    for cnae in cnaes:
        supplier.append("cnaes", {
            "cnae_code": cnae.get("cnae_code", ""),
            "description": cnae.get("description", ""),
            "is_primary": cnae.get("is_primary", 0),
        })


def _criar_endereco(supplier_name: str, dados: dict) -> str | None:
    endereco = dados.get("endereco", {})
    address_line1 = endereco.get("address_line1", "")
    city = endereco.get("city", "")

    if not address_line1:
        address_line1 = endereco.get("address_line2", "") or "Endereço não informado"

    if not city:
        city = endereco.get("state", "") or "Não informado"

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
    address.address_line2 = endereco.get("address_line2", "")
    address.city = city
    address.state = endereco.get("state", "")
    address.country = "Brazil"
    address.pincode = endereco.get("pincode", "")
    address.phone = endereco.get("phone", "")
    address.email_id = endereco.get("email_id", "")
    address.is_primary_address = 1
    address.is_shipping_address = 0
    address.save(ignore_permissions=True)
    return address.name


def _criar_contato(supplier_name: str, dados: dict) -> str | None:
    socios = dados.get("socios", [])
    telefone = dados.get("telefone_1", "")
    email = dados.get("email", "")

    if not socios and not telefone and not email:
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

    if socios:
        nome_completo = socios[0].get("nome", "")
        partes = nome_completo.strip().split()
        if partes:
            contact.first_name = partes[0]
            if len(partes) > 1:
                contact.last_name = " ".join(partes[1:])
        contact.designation = socios[0].get("qualificacao", "")
    else:
        contact.first_name = supplier_name

    contact.status = "Passive"
    contact.is_primary_contact = 1

    if telefone:
        contact.append("phone_nos", {"phone": telefone, "is_primary_phone": 1})

    if email:
        contact.append("email_ids", {"email_id": email, "is_primary": 1})

    contact.save(ignore_permissions=True)
    return contact.name
