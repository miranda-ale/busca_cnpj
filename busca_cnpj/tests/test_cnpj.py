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


if __name__ == "__main__":
	unittest.main()
