import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


CUSTOM_FIELDS = {
    "Supplier": [
        {
            "fieldname": "cnae_section",
            "fieldtype": "Section Break",
            "label": "CNAEs",
            "insert_after": "tax_id",
            "collapsible": 1,
        },
        {
            "fieldname": "cnaes",
            "fieldtype": "Table",
            "label": "CNAEs",
            "options": "CNAE Fornecedor",
            "insert_after": "cnae_section",
        },
    ],
    "Address": [
        {
            "fieldname": "custom_bairro",
            "fieldtype": "Data",
            "label": "Bairro",
            "insert_after": "address_line2",
        },
    ],
}


def after_install():
    create_custom_fields(CUSTOM_FIELDS, update=True)
    ajustar_layout_address()
    desativar_scripts_cnpj_legado()


def ajustar_layout_address():
    """Rotula o CEP e o coloca logo abaixo do tipo de endereço, antes do logradouro."""
    make_property_setter("Address", "pincode", "label", "CEP", "Data")

    campos = [df.fieldname for df in frappe.get_meta("Address", cached=False).fields]
    if "pincode" not in campos or "address_type" not in campos:
        return
    campos.remove("pincode")
    campos.insert(campos.index("address_type") + 1, "pincode")

    atual = frappe.db.get_value(
        "Property Setter",
        {"doc_type": "Address", "doctype_or_field": "DocType", "property": "field_order"},
        "value",
    )
    if atual and json.loads(atual) == campos:
        return
    make_property_setter("Address", None, "field_order", json.dumps(campos), "Data", for_doctype=True)


def after_migrate():
    after_install()


LEGACY_MARKERS = (
    "números digitados",
    "numeros digitados",
    "verifique os números digitados",
    "verifique os numeros digitados",
    "is_valid_cnpj",
    "cnpj.length !== 14",
    "cnpj.length != 14",
)


def desativar_scripts_cnpj_legado():
    """Desliga Client/Server Script do site que ainda validam CNPJ só com dígitos."""
    _desativar_client_scripts()
    _desativar_server_scripts()


def _texto_legado(script: str) -> bool:
    texto = (script or "").lower()
    if any(m in texto for m in LEGACY_MARKERS):
        return True
    if "cnpj inválido" in texto or "cnpj invalido" in texto:
        ascii_novo = "charcodeat" in texto or "ord(" in texto or "- 48" in texto
        return not ascii_novo
    return False


def _desativar_client_scripts():
    if not frappe.db.exists("DocType", "Client Script"):
        return
    scripts = frappe.get_all(
        "Client Script",
        filters={"dt": "Supplier", "enabled": 1},
        fields=["name", "script"],
    )
    for row in scripts:
        if not _texto_legado(row.script):
            continue
        frappe.db.set_value("Client Script", row.name, "enabled", 0, update_modified=False)
        frappe.logger("busca_cnpj").info("Client Script legado desativado: %s", row.name)


def _desativar_server_scripts():
    if not frappe.db.exists("DocType", "Server Script"):
        return
    scripts = frappe.get_all(
        "Server Script",
        filters={"reference_doctype": "Supplier", "disabled": 0},
        fields=["name", "script"],
    )
    for row in scripts:
        if not _texto_legado(row.script):
            continue
        frappe.db.set_value("Server Script", row.name, "disabled", 1, update_modified=False)
        frappe.logger("busca_cnpj").info("Server Script legado desativado: %s", row.name)
