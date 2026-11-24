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
	"Employee": [
		{
			"fieldname": "custom_current_cep",
			"fieldtype": "Data",
			"label": "CEP (Endereço Atual)",
			"insert_after": "address_section",
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
	adjust_address_layout()
	disable_legacy_cnpj_scripts()


def adjust_address_layout():
	"""Label the postal code (CEP) and place it right below the address type, before the street line."""
	make_property_setter("Address", "pincode", "label", "CEP", "Data")

	fieldnames = [df.fieldname for df in frappe.get_meta("Address", cached=False).fields]
	if "pincode" not in fieldnames or "address_type" not in fieldnames:
		return
	fieldnames.remove("pincode")
	fieldnames.insert(fieldnames.index("address_type") + 1, "pincode")

	current = frappe.db.get_value(
		"Property Setter",
		{"doc_type": "Address", "doctype_or_field": "DocType", "property": "field_order"},
		"value",
	)
	if current and json.loads(current) == fieldnames:
		return
	make_property_setter("Address", None, "field_order", json.dumps(fieldnames), "Data", for_doctype=True)


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


def disable_legacy_cnpj_scripts():
	"""Disable site Client/Server Scripts that still validate CNPJ with digits only."""
	_disable_client_scripts()
	_disable_server_scripts()


def _is_legacy_script(script: str) -> bool:
	text = (script or "").lower()
	if any(m in text for m in LEGACY_MARKERS):
		return True
	if "cnpj inválido" in text or "cnpj invalido" in text:
		has_new_ascii_logic = "charcodeat" in text or "ord(" in text or "- 48" in text
		return not has_new_ascii_logic
	return False


def _disable_client_scripts():
	if not frappe.db.exists("DocType", "Client Script"):
		return
	scripts = frappe.get_all(
		"Client Script",
		filters={"dt": "Supplier", "enabled": 1},
		fields=["name", "script"],
	)
	for row in scripts:
		if not _is_legacy_script(row.script):
			continue
		frappe.db.set_value("Client Script", row.name, "enabled", 0, update_modified=False)
		frappe.logger("busca_cnpj").info("Client Script legado desativado: %s", row.name)


def _disable_server_scripts():
	if not frappe.db.exists("DocType", "Server Script"):
		return
	scripts = frappe.get_all(
		"Server Script",
		filters={"reference_doctype": "Supplier", "disabled": 0},
		fields=["name", "script"],
	)
	for row in scripts:
		if not _is_legacy_script(row.script):
			continue
		frappe.db.set_value("Server Script", row.name, "disabled", 1, update_modified=False)
		frappe.logger("busca_cnpj").info("Server Script legado desativado: %s", row.name)


# Deprecated aliases kept for the old public names; remove after external callers migrate.
ajustar_layout_address = adjust_address_layout
desativar_scripts_cnpj_legado = disable_legacy_cnpj_scripts
