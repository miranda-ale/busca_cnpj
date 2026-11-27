# Copyright (c) 2026, StillPulse Tecnologia LTDA and contributors
# For license information, please see license.txt

import inspect
import json
import unittest
from unittest import mock

from busca_cnpj.cnpj import character_value, format_cnpj, normalize_cnpj, validate_cnpj


class TestAlphanumericCnpj(unittest.TestCase):
	def test_normalizes_mask_and_lowercase(self):
		self.assertEqual(normalize_cnpj("00.000.000/E08G-12"), "00000000E08G12")
		self.assertEqual(normalize_cnpj("00.000.000/e08g-12"), "00000000E08G12")

	def test_keeps_letters(self):
		self.assertEqual(normalize_cnpj("00000000E08G12"), "00000000E08G12")

	def test_character_value_is_ascii_minus_48(self):
		self.assertEqual(character_value("0"), 0)
		self.assertEqual(character_value("9"), 9)
		self.assertEqual(character_value("A"), 17)
		self.assertEqual(character_value("E"), 21)
		self.assertEqual(character_value("G"), 23)

	def test_first_official_alphanumeric_cnpj(self):
		# Brazilian Federal Revenue Service, 2026-07-31: Banco do Brasil branch
		self.assertTrue(validate_cnpj("00.000.000/E08G-12"))
		self.assertTrue(validate_cnpj("00000000E08G12"))

	def test_numeric_cnpj_still_valid(self):
		self.assertTrue(validate_cnpj("00.000.000/0001-91"))

	def test_invalid_check_digit(self):
		self.assertFalse(validate_cnpj("00.000.000/E08G-99"))
		self.assertFalse(validate_cnpj("00.000.000/0001-00"))

	def test_wrong_length_and_non_numeric_check_digit(self):
		self.assertFalse(validate_cnpj("00000000E08G1"))
		self.assertFalse(validate_cnpj("00000000E08GA2"))

	def test_formatting(self):
		self.assertEqual(format_cnpj("00000000E08G12"), "00.000.000/E08G-12")
		self.assertEqual(format_cnpj("00000000000191"), "00.000.000/0001-91")

	def test_tax_id_empty_and_alphanumeric(self):
		from busca_cnpj.cnpj import validate_tax_id

		self.assertTrue(validate_tax_id(""))
		self.assertTrue(validate_tax_id("00.000.000/E08G-12"))
		self.assertTrue(validate_tax_id("00.000.000/0001-91"))
		self.assertFalse(validate_tax_id("00.000.000/E08G-99"))

	def test_deprecated_portuguese_aliases(self):
		from busca_cnpj import cnpj

		self.assertIs(cnpj.validar_cnpj, cnpj.validate_cnpj)
		self.assertIs(cnpj.formatar_cnpj, cnpj.format_cnpj)
		self.assertIs(cnpj.normalizar_cnpj, cnpj.normalize_cnpj)
		self.assertIs(cnpj.validar_cpf, cnpj.validate_cpf)

	def test_validar_tax_id_alias_accepts_valor_keyword(self):
		from busca_cnpj import cnpj

		self.assertTrue(cnpj.validar_tax_id(valor="00.000.000/0001-91"))
		self.assertTrue(cnpj.validar_tax_id("00.000.000/0001-91"))
		self.assertFalse(cnpj.validar_tax_id(valor="00.000.000/E08G-99"))

	def test_character_value_alias(self):
		from busca_cnpj import cnpj

		self.assertIs(cnpj.valor_caractere, cnpj.character_value)


class TestDeprecatedApiAliases(unittest.TestCase):
	"""Public names from the pre-rename main must stay importable (offline, no bench needed)."""

	EXPECTED_API_NAMES = (
		"buscar_cnpj",
		"buscar_cep",
		"confirmar_dados_cnpj",
		"formatar_cep",
		"formatar_telefone",
		"sanitizar_razao_social",
		"BRASILAPI_BASE_URL",
		"MINHA_RECEITA_BASE_URL",
		"CNPJWS_BASE_URL",
		"VIACEP_BASE_URL",
		"SAVEPOINT_RENOMEAR_SUPPLIER",
	)
	EXPECTED_CNPJ_NAMES = (
		"normalizar_cnpj",
		"valor_caractere",
		"validar_cnpj",
		"formatar_cnpj",
		"validar_cpf",
		"validar_tax_id",
		"CNPJ_WEIGHTS_1",
		"CNPJ_WEIGHTS_2",
	)
	EXPECTED_SETUP_NAMES = (
		"after_install",
		"after_migrate",
		"ajustar_layout_address",
		"desativar_scripts_cnpj_legado",
		"CUSTOM_FIELDS",
		"LEGACY_MARKERS",
	)

	def _load(self, name):
		import importlib

		try:
			return importlib.import_module(name)
		except ModuleNotFoundError as exc:
			self.skipTest(f"{name} needs frappe: {exc}")

	def test_no_public_name_removed(self):
		for module_name, names in (
			("busca_cnpj.api", self.EXPECTED_API_NAMES),
			("busca_cnpj.cnpj", self.EXPECTED_CNPJ_NAMES),
			("busca_cnpj.setup", self.EXPECTED_SETUP_NAMES),
			("busca_cnpj.supplier_validate", ("validate_supplier",)),
		):
			module = self._load(module_name)
			for name in names:
				self.assertTrue(hasattr(module, name), f"{module_name}.{name} is missing")

	def test_buscar_cep_delegates_to_lookup_cep(self):
		from unittest.mock import patch

		api = self._load("busca_cnpj.api")
		with patch.object(api, "lookup_cep", return_value={"pincode": "01001-000"}) as mocked:
			self.assertEqual(api.buscar_cep("01001000"), {"pincode": "01001-000"})
		mocked.assert_called_once_with("01001000")

	def test_buscar_cnpj_delegates_to_lookup_cnpj(self):
		from unittest.mock import patch

		api = self._load("busca_cnpj.api")
		with patch.object(api, "lookup_cnpj", return_value={"ok": 1}) as mocked:
			self.assertEqual(api.buscar_cnpj("00000000000191"), {"ok": 1})
		mocked.assert_called_once_with("00000000000191")


class TestConfirmCnpjData(unittest.TestCase):
	"""Regression for the Semgrep findings: no manual commit and no GET on a method that writes."""

	def setUp(self):
		try:
			import frappe

			from busca_cnpj import api
		except ModuleNotFoundError as exc:
			self.skipTest(f"needs frappe: {exc}")
		self.frappe = frappe
		self.api = api

	def test_post_only_for_new_name_and_alias(self):
		allowed = getattr(self.frappe, "allowed_http_methods_for_whitelisted_func", None)
		if allowed is None:
			self.skipTest("frappe.allowed_http_methods_for_whitelisted_func not available (stub frappe)")
		self.assertEqual(allowed[self.api.confirm_cnpj_data], ["POST"])
		self.assertEqual(allowed[self.api.confirmar_dados_cnpj], ["POST"])

	def _confirm(self, function_name, rename_error):
		"""Run the confirmation with a failing rename; return (result, error, savepoint, rollback, commit)."""
		api = self.api
		supplier = mock.MagicMock()
		supplier.name = "Antigo"
		data = {"razao_social": "Novo", "cnpj_formatado": "00.000.000/0001-91"}
		with (
			mock.patch.object(api.frappe.defaults, "get_global_default", return_value="Supplier Name"),
			mock.patch.object(api.frappe, "get_doc", return_value=supplier),
			mock.patch.object(api.frappe, "rename_doc", side_effect=rename_error),
			mock.patch.object(api.frappe, "log_error"),
			mock.patch.object(api.frappe.db, "exists", return_value=None),
			mock.patch.object(api.frappe.db, "savepoint") as savepoint,
			mock.patch.object(api.frappe.db, "rollback") as rollback,
			mock.patch.object(api.frappe.db, "commit") as commit,
			mock.patch.object(api, "_create_address", return_value=None),
			mock.patch.object(api, "_create_contact", return_value=None),
		):
			try:
				result = getattr(api, function_name)("Antigo", json.dumps(data))
				error = None
			except Exception as exc:
				result, error = None, exc
		return result, error, savepoint, rollback, commit

	def test_duplicate_rename_undoes_only_the_rename_without_commit(self):
		for function_name in ("confirm_cnpj_data", "confirmar_dados_cnpj"):
			result, error, savepoint, rollback, commit = self._confirm(
				function_name, self.frappe.DuplicateEntryError
			)
			self.assertIsNone(error)
			commit.assert_not_called()
			savepoint.assert_called_once_with(self.api.SAVEPOINT_RENAME_SUPPLIER)
			rollback.assert_called_once_with(save_point=self.api.SAVEPOINT_RENAME_SUPPLIER)
			self.assertEqual(result["supplier"], "Antigo")

	def test_validation_error_in_rename_rolls_back_and_propagates(self):
		for function_name in ("confirm_cnpj_data", "confirmar_dados_cnpj"):
			_, error, _, rollback, commit = self._confirm(
				function_name, self.frappe.ValidationError("invalid rename")
			)
			self.assertIsInstance(error, self.frappe.ValidationError)
			commit.assert_not_called()
			rollback.assert_called_once_with(save_point=self.api.SAVEPOINT_RENAME_SUPPLIER)

	def test_no_manual_commit_in_module(self):
		self.assertNotIn("db.commit", inspect.getsource(self.api))


if __name__ == "__main__":
	unittest.main()
