"""Phase 2: DocType "CNAE Fornecedor" (child table of Supplier.cnaes) -> "CNPJ Supplier CNAE".

[pre_model_sync] so the renamed standard files sync onto the renamed DocType. frappe.rename_doc renames the table, the
Custom Field options and the child rows' parenttype references. Idempotent.
"""

import frappe

OLD, NEW = "CNAE Fornecedor", "CNPJ Supplier CNAE"


def execute():
	if frappe.db.exists("DocType", OLD) and not frappe.db.exists("DocType", NEW):
		frappe.rename_doc("DocType", OLD, NEW, force=True)
