import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


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
}


def after_install():
    create_custom_fields(CUSTOM_FIELDS, update=True)


def after_migrate():
    after_install()
