# Copyright (c) 2026, Still Pulse and contributors
# For license information, please see license.txt

import unittest

from busca_cnpj.cnpj import formatar_cnpj, normalizar_cnpj, validar_cnpj, valor_caractere


class TestCnpjAlfanumerico(unittest.TestCase):
	def test_normaliza_mascara_e_minusculas(self):
		self.assertEqual(normalizar_cnpj("00.000.000/E08G-12"), "00000000E08G12")
		self.assertEqual(normalizar_cnpj("00.000.000/e08g-12"), "00000000E08G12")

	def test_nao_descarta_letras(self):
		self.assertEqual(normalizar_cnpj("00000000E08G12"), "00000000E08G12")

	def test_valor_ascii_menos_48(self):
		self.assertEqual(valor_caractere("0"), 0)
		self.assertEqual(valor_caractere("9"), 9)
		self.assertEqual(valor_caractere("A"), 17)
		self.assertEqual(valor_caractere("E"), 21)
		self.assertEqual(valor_caractere("G"), 23)

	def test_primeiro_cnpj_alfanumerico_oficial(self):
		# Receita Federal, 31/07/2026 — filial Banco do Brasil
		self.assertTrue(validar_cnpj("00.000.000/E08G-12"))
		self.assertTrue(validar_cnpj("00000000E08G12"))

	def test_cnpj_numerico_ainda_valido(self):
		self.assertTrue(validar_cnpj("00.000.000/0001-91"))

	def test_dv_invalido(self):
		self.assertFalse(validar_cnpj("00.000.000/E08G-99"))
		self.assertFalse(validar_cnpj("00.000.000/0001-00"))

	def test_tamanho_e_dv_nao_numerico(self):
		self.assertFalse(validar_cnpj("00000000E08G1"))
		self.assertFalse(validar_cnpj("00000000E08GA2"))

	def test_formatacao(self):
		self.assertEqual(formatar_cnpj("00000000E08G12"), "00.000.000/E08G-12")
		self.assertEqual(formatar_cnpj("00000000000191"), "00.000.000/0001-91")

	def test_tax_id_vazio_e_alfanumerico(self):
		from busca_cnpj.cnpj import validar_tax_id

		self.assertTrue(validar_tax_id(""))
		self.assertTrue(validar_tax_id("00.000.000/E08G-12"))
		self.assertTrue(validar_tax_id("00.000.000/0001-91"))
		self.assertFalse(validar_tax_id("00.000.000/E08G-99"))


if __name__ == "__main__":
	unittest.main()
