"""Email authentication header parser service."""

import re
from typing import Dict


class EmailAuthParser:
	"""Parse email authentication headers and extract trust information."""

	@staticmethod
	def parse_authentication_results(auth_header: str) -> Dict[str, str]:
		result = {
			"spf": "NONE",
			"dkim": "NONE",
			"dmarc": "NONE",
		}

		if not auth_header:
			return result

		spf_match = re.search(r"\bspf=(\w+)", auth_header, re.IGNORECASE)
		if spf_match:
			result["spf"] = spf_match.group(1).upper()

		dkim_match = re.search(r"\bdkim=(\w+)", auth_header, re.IGNORECASE)
		if dkim_match:
			result["dkim"] = dkim_match.group(1).upper()

		dmarc_match = re.search(r"\bdmarc=(\w+)", auth_header, re.IGNORECASE)
		if dmarc_match:
			result["dmarc"] = dmarc_match.group(1).upper()

		return result

	@staticmethod
	def parse_dkim_signature(dkim_header: str) -> Dict[str, str]:
		result = {
			"domain": None,
			"algorithm": None,
			"signed": False,
		}

		if not dkim_header:
			return result

		result["signed"] = True

		d_match = re.search(r"\bd=([^;]+)", dkim_header)
		if d_match:
			result["domain"] = d_match.group(1).strip()

		a_match = re.search(r"\ba=([^;]+)", dkim_header)
		if a_match:
			result["algorithm"] = a_match.group(1).strip()

		return result

	@staticmethod
	def extract_auth_headers(headers: Dict[str, str]) -> Dict:
		normalized_headers = {k.lower(): v for k, v in headers.items()}

		auth_results = normalized_headers.get("authentication-results", "")
		dkim_sig = normalized_headers.get("dkim-signature", "")
		received_spf = normalized_headers.get("received-spf", "")

		return {
			"authentication_results": EmailAuthParser.parse_authentication_results(auth_results),
			"dkim_signature": EmailAuthParser.parse_dkim_signature(dkim_sig),
			"raw_headers": {
				"authentication_results": auth_results,
				"dkim_signature": dkim_sig,
				"received_spf": received_spf,
			},
		}

	@staticmethod
	def calculate_trust_score(
		spf_status: str = "NONE",
		dkim_status: str = "NONE",
		dmarc_status: str = "NONE",
		dkim_signed: bool = False,
		domain_age_days: int = 0,
	) -> int:
		score = 30

		if spf_status == "PASS":
			score += 30
		elif spf_status == "FAIL":
			score -= 20
		elif spf_status in ["SOFTFAIL", "NEUTRAL"]:
			score += 5

		if dkim_status == "PASS":
			score += 30
		elif dkim_status == "FAIL":
			score -= 20
		elif dkim_signed:
			score += 5

		if dmarc_status == "PASS":
			score += 20
		elif dmarc_status == "FAIL":
			score -= 15

		if domain_age_days > 180:
			score += 5

		return max(0, min(100, score))

	@staticmethod
	def is_verified(spf_status: str, dkim_status: str, dmarc_status: str) -> bool:
		return (
			spf_status == "PASS"
			and dkim_status == "PASS"
			and dmarc_status == "PASS"
		)


def parse_email_auth(message_dict: Dict) -> Dict:
	parser = EmailAuthParser()
	headers = message_dict.get("headers", {})

	auth_data = parser.extract_auth_headers(headers)
	auth_results = auth_data["authentication_results"]
	dkim_sig = auth_data["dkim_signature"]

	spf_status = auth_results.get("spf", "NONE")
	dkim_status = auth_results.get("dkim", "NONE")
	dmarc_status = auth_results.get("dmarc", "NONE")
	dkim_signed = dkim_sig.get("signed", False)

	trust_score = parser.calculate_trust_score(
		spf_status=spf_status,
		dkim_status=dkim_status,
		dmarc_status=dmarc_status,
		dkim_signed=dkim_signed,
	)

	is_verified = parser.is_verified(spf_status, dkim_status, dmarc_status)

	return {
		"spf_status": spf_status,
		"dkim_status": dkim_status,
		"dmarc_status": dmarc_status,
		"auth_score": trust_score,
		"is_verified": is_verified,
		"dkim_signed": dkim_signed,
		"auth_headers": auth_data["raw_headers"],
	}


__all__ = ["EmailAuthParser", "parse_email_auth"]
