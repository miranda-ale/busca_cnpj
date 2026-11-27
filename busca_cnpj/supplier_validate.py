# Copyright (c) 2026, StillPulse Tecnologia LTDA and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from busca_cnpj.cnpj import validate_tax_id


def validate_supplier(doc, method=None):
	if not doc.tax_id:
		return
	if validate_tax_id(doc.tax_id):
		return
	frappe.throw(_("CNPJ/CPF inválido: {0}. Verifique os dígitos informados.").format(doc.tax_id))
