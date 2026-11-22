# Copyright (c) 2026, Still Pulse and contributors
# For license information, please see license.txt

import inspect
import json
import unittest
from unittest import mock

import frappe

from busca_cnpj import api
from busca_cnpj.api import confirmar_dados_cnpj
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


class TestConfirmarDadosCnpj(unittest.TestCase):
	"""Regressão dos achados do Semgrep: sem commit manual e sem GET em método que grava."""

	def test_so_aceita_post(self):
		self.assertEqual(frappe.allowed_http_methods_for_whitelisted_func[confirmar_dados_cnpj], ["POST"])

	def _confirmar(self, rename_erro):
		"""Roda a confirmação com rename que falha; devolve (resultado, mocks de savepoint/rollback/commit)."""
		supplier = mock.MagicMock()
		supplier.name = "Antigo"
		dados = {"razao_social": "Novo", "cnpj_formatado": "00.000.000/0001-91"}
		with (
			mock.patch.object(api.frappe.defaults, "get_global_default", return_value="Supplier Name"),
			mock.patch.object(api.frappe, "get_doc", return_value=supplier),
			mock.patch.object(api.frappe, "rename_doc", side_effect=rename_erro),
			mock.patch.object(api.frappe, "log_error"),
			mock.patch.object(api.frappe.db, "exists", return_value=None),
			mock.patch.object(api.frappe.db, "savepoint") as savepoint,
			mock.patch.object(api.frappe.db, "rollback") as rollback,
			mock.patch.object(api.frappe.db, "commit") as commit,
			mock.patch.object(api, "_criar_endereco", return_value=None),
			mock.patch.object(api, "_criar_contato", return_value=None),
		):
			try:
				resultado = api.confirmar_dados_cnpj("Antigo", json.dumps(dados))
				erro = None
			except Exception as e:
				resultado, erro = None, e
		return resultado, erro, savepoint, rollback, commit

	def test_rename_duplicado_desfaz_so_o_rename_sem_commit(self):
		resultado, erro, savepoint, rollback, commit = self._confirmar(frappe.DuplicateEntryError)
		self.assertIsNone(erro)
		commit.assert_not_called()
		savepoint.assert_called_once_with(api.SAVEPOINT_RENOMEAR_SUPPLIER)
		rollback.assert_called_once_with(save_point=api.SAVEPOINT_RENOMEAR_SUPPLIER)
		self.assertEqual(resultado["supplier"], "Antigo")

	def test_erro_de_validacao_no_rename_desfaz_o_rename_e_propaga(self):
		_, erro, _, rollback, commit = self._confirmar(frappe.ValidationError("rename inválido"))
		self.assertIsInstance(erro, frappe.ValidationError)
		commit.assert_not_called()
		rollback.assert_called_once_with(save_point=api.SAVEPOINT_RENOMEAR_SUPPLIER)

	def test_sem_commit_manual_no_modulo(self):
		self.assertNotIn("db.commit", inspect.getsource(api))


if __name__ == "__main__":
	unittest.main()
