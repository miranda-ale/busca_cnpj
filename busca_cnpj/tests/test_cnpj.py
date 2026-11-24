# Copyright (c) 2026, StillPulse Tecnologia LTDA and contributors
# For license information, please see license.txt

import unittest

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
		self.assertIs(cnpj.validar_tax_id, cnpj.validate_tax_id)

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


if __name__ == "__main__":
	unittest.main()
