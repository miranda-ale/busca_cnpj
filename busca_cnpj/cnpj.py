# Copyright (c) 2026, StillPulse Tecnologia LTDA and contributors
# For license information, please see license.txt

"""Normalization, formatting and check digits for numeric and alphanumeric CNPJ.

Brazilian Federal Revenue Service (Receita Federal): the first 12 characters may be A-Z/0-9;
the last 2 (check digits) remain numeric. Character value = ASCII - 48.
Legacy numeric-only CNPJs remain valid under the same algorithm.
"""

from __future__ import annotations

import re

CNPJ_WEIGHTS_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ_WEIGHTS_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

_CNPJ_BASE_RE = re.compile(r"[^A-Z0-9]")


def normalize_cnpj(cnpj: str | None) -> str:
	"""Strip the mask and return up to 14 uppercase A-Z/0-9 characters."""
	return _CNPJ_BASE_RE.sub("", (cnpj or "").upper())


def character_value(char: str) -> int:
	"""Official character value for the check digit (ASCII - 48)."""
	return ord(char) - 48


def _calc_check_digit(base: str, weights: list[int]) -> int:
	total = sum(character_value(base[i]) * weights[i] for i in range(len(weights)))
	remainder = total % 11
	return 0 if remainder < 2 else 11 - remainder


def validate_cnpj(cnpj: str | None) -> bool:
	base = normalize_cnpj(cnpj)
	if len(base) != 14:
		return False
	if not re.fullmatch(r"[A-Z0-9]{12}\d{2}", base):
		return False
	if base == base[0] * 14:
		return False
	if _calc_check_digit(base[:12], CNPJ_WEIGHTS_1) != int(base[12]):
		return False
	if _calc_check_digit(base[:13], CNPJ_WEIGHTS_2) != int(base[13]):
		return False
	return True


def format_cnpj(cnpj: str | None) -> str:
	base = normalize_cnpj(cnpj)
	if len(base) != 14:
		return cnpj or ""
	return f"{base[:2]}.{base[2:5]}.{base[5:8]}/{base[8:12]}-{base[12:]}"


def validate_cpf(cpf: str | None) -> bool:
	digits = re.sub(r"\D", "", cpf or "")
	if len(digits) != 11 or digits == digits[0] * 11:
		return False
	for length, weight_start in ((9, 10), (10, 11)):
		total = sum(int(digits[i]) * (weight_start - i) for i in range(length))
		check_digit = (total * 10) % 11
		if check_digit == 10:
			check_digit = 0
		if check_digit != int(digits[length]):
			return False
	return True


def validate_tax_id(value: str | None) -> bool:
	"""CPF (11 digits) or numeric/alphanumeric CNPJ (14). Empty is valid."""
	if not (value or "").strip():
		return True
	base = normalize_cnpj(value)
	if len(base) == 11 and base.isdigit():
		return validate_cpf(base)
	if len(base) == 14:
		return validate_cnpj(base)
	return False


# Deprecated Portuguese aliases kept for external consumers (integracoes_customizadas imports
# `formatar_cnpj`, `normalizar_cnpj`, `validar_tax_id` and `validar_cpf`). Remove once they migrate.
normalizar_cnpj = normalize_cnpj
validar_cnpj = validate_cnpj
formatar_cnpj = format_cnpj
validar_cpf = validate_cpf
validar_tax_id = validate_tax_id
