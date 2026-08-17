# Copyright (c) 2026, Still Pulse and contributors
# For license information, please see license.txt

"""Normalização, formatação e DV do CNPJ numérico e alfanumérico.

Receita Federal: os 12 primeiros caracteres podem ser A-Z/0-9;
os 2 últimos (DV) continuam numéricos. Valor do caractere = ASCII - 48.
CNPJs antigos (só números) continuam válidos com o mesmo algoritmo.
"""

from __future__ import annotations

import re

CNPJ_WEIGHTS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ_WEIGHTS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

_CNPJ_BASE_RE = re.compile(r"[^A-Z0-9]")


def normalizar_cnpj(cnpj: str | None) -> str:
	"""Remove máscara e deixa 14 caracteres A-Z/0-9 em maiúsculas."""
	return _CNPJ_BASE_RE.sub("", (cnpj or "").upper())


def valor_caractere(char: str) -> int:
	"""Valor oficial do caractere para o DV (ASCII - 48)."""
	return ord(char) - 48


def _calc_dv(base: str, weights: list[int]) -> int:
	total = sum(valor_caractere(base[i]) * weights[i] for i in range(len(weights)))
	remainder = total % 11
	return 0 if remainder < 2 else 11 - remainder


def validar_cnpj(cnpj: str | None) -> bool:
	base = normalizar_cnpj(cnpj)
	if len(base) != 14:
		return False
	if not re.fullmatch(r"[A-Z0-9]{12}\d{2}", base):
		return False
	if base == base[0] * 14:
		return False
	if _calc_dv(base[:12], CNPJ_WEIGHTS_1) != int(base[12]):
		return False
	if _calc_dv(base[:13], CNPJ_WEIGHTS_2) != int(base[13]):
		return False
	return True


def formatar_cnpj(cnpj: str | None) -> str:
	base = normalizar_cnpj(cnpj)
	if len(base) != 14:
		return cnpj or ""
	return f"{base[:2]}.{base[2:5]}.{base[5:8]}/{base[8:12]}-{base[12:]}"


def validar_cpf(cpf: str | None) -> bool:
	digits = re.sub(r"\D", "", cpf or "")
	if len(digits) != 11 or digits == digits[0] * 11:
		return False
	for turn, pos in ((9, 10), (10, 11)):
		total = sum(int(digits[i]) * (pos - i) for i in range(turn))
		dv = (total * 10) % 11
		if dv == 10:
			dv = 0
		if dv != int(digits[turn]):
			return False
	return True


def validar_tax_id(valor: str | None) -> bool:
	"""CPF (11 dígitos) ou CNPJ numérico/alfanumérico (14). Vazio é válido."""
	if not (valor or "").strip():
		return True
	base = normalizar_cnpj(valor)
	if len(base) == 11 and base.isdigit():
		return validar_cpf(base)
	if len(base) == 14:
		return validar_cnpj(base)
	return False
