"""
Email authentication header parser.

Extracts SPF, DKIM, DMARC status from Authentication-Results header
and other security headers (DKIM-Signature, etc).
"""

import re
from typing import Dict, Optional, List
from datetime import datetime


class EmailAuthParser:
    """Parse email authentication headers and extract trust information."""
    
    @staticmethod
    def parse_authentication_results(auth_header: str) -> Dict[str, str]:
        """
        Parse Authentication-Results header.
        
        Example header:
        spf=pass (google.com: domain of sender@example.com designates 1.2.3.4 as permitted sender)
        dkim=pass header.i=@example.com header.s=default header.b=abcdef123;
        dmarc=pass (p=NONE sp=QUARANTINE dis=NONE) header.from=example.com
        
        Returns:
            Dict with keys: spf, dkim, dmarc (values: PASS, FAIL, NEUTRAL, SOFTFAIL, NONE)
        """
        result = {
            "spf": "NONE",
            "dkim": "NONE", 
            "dmarc": "NONE"
        }
        
        if not auth_header:
            return result
        
        # Extract SPF status
        spf_match = re.search(r'\bspf=(\w+)', auth_header, re.IGNORECASE)
        if spf_match:
            result["spf"] = spf_match.group(1).upper()
        
        # Extract DKIM status
        dkim_match = re.search(r'\bdkim=(\w+)', auth_header, re.IGNORECASE)
        if dkim_match:
            result["dkim"] = dkim_match.group(1).upper()
        
        # Extract DMARC status
        dmarc_match = re.search(r'\bdmarc=(\w+)', auth_header, re.IGNORECASE)
        if dmarc_match:
            result["dmarc"] = dmarc_match.group(1).upper()
        
        return result
    
    @staticmethod
    def parse_dkim_signature(dkim_header: str) -> Dict[str, str]:
        """Parse DKIM-Signature header to extract signing domain and algorithm."""
        result = {
            "domain": None,
            "algorithm": None,
            "signed": False
        }
        
        if not dkim_header:
            return result
        
        result["signed"] = True
        
        # Extract d= (domain)
        d_match = re.search(r'\bd=([^;]+)', dkim_header)
        if d_match:
            result["domain"] = d_match.group(1).strip()
        
        # Extract a= (algorithm)
        a_match = re.search(r'\ba=([^;]+)', dkim_header)
        if a_match:
            result["algorithm"] = a_match.group(1).strip()
        
        return result
    
    @staticmethod
    def extract_auth_headers(headers: Dict[str, str]) -> Dict:
        """
        Extract relevant authentication headers from email headers dict.
        
        Args:
            headers: Dict of email headers (case-insensitive)
            
        Returns:
            Dict with parsed auth information
        """
        # Normalize header names to lowercase for searching
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        
        auth_results = normalized_headers.get("authentication-results", "")
        dkim_sig = normalized_headers.get("dkim-signature", "")
        received_spf = normalized_headers.get("received-spf", "")
        
        parsed = {
            "authentication_results": EmailAuthParser.parse_authentication_results(auth_results),
            "dkim_signature": EmailAuthParser.parse_dkim_signature(dkim_sig),
            "raw_headers": {
                "authentication_results": auth_results,
                "dkim_signature": dkim_sig,
                "received_spf": received_spf
            }
        }
        
        return parsed
    
    @staticmethod
    def calculate_trust_score(
        spf_status: str = "NONE",
        dkim_status: str = "NONE",
        dmarc_status: str = "NONE",
        dkim_signed: bool = False,
        domain_age_days: int = 0
    ) -> int:
        """
        Calculate a trust score (0-100) based on authentication results.
        
        Scoring:
        - SPF PASS: +30 points
        - DKIM PASS: +30 points
        - DMARC PASS: +20 points
        - DKIM signed (even if not passing): +5 points
        - SPF SOFTFAIL/NEUTRAL: +5 points
        - SPF FAIL: -20 points
        - DKIM FAIL: -20 points
        - DMARC FAIL: -15 points
        
        Minimum: 0, Maximum: 100
        """
        score = 30  # Start with baseline trust
        
        # SPF scoring
        if spf_status == "PASS":
            score += 30
        elif spf_status == "FAIL":
            score -= 20
        elif spf_status in ["SOFTFAIL", "NEUTRAL"]:
            score += 5
        
        # DKIM scoring
        if dkim_status == "PASS":
            score += 30
        elif dkim_status == "FAIL":
            score -= 20
        elif dkim_signed:
            score += 5
        
        # DMARC scoring
        if dmarc_status == "PASS":
            score += 20
        elif dmarc_status == "FAIL":
            score -= 15
        
        # Domain age bonus (domains older than 6 months get +5 points)
        if domain_age_days > 180:
            score += 5
        
        # Clamp score between 0 and 100
        return max(0, min(100, score))
    
    @staticmethod
    def is_verified(spf_status: str, dkim_status: str, dmarc_status: str) -> bool:
        """Check if email passes all three authentication methods."""
        return (
            spf_status == "PASS" and
            dkim_status == "PASS" and
            dmarc_status == "PASS"
        )


def parse_email_auth(message_dict: Dict) -> Dict:
    """
    Extract authentication information from a Gmail message.
    
    Args:
        message_dict: Gmail message dict with 'headers' key
        
    Returns:
        Dict with auth_status, spf_status, dkim_status, dmarc_status, auth_score, is_verified
    """
    parser = EmailAuthParser()
    
    # Get headers from message
    headers = message_dict.get("headers", {})
    
    # Extract auth data
    auth_data = parser.extract_auth_headers(headers)
    auth_results = auth_data["authentication_results"]
    dkim_sig = auth_data["dkim_signature"]
    
    # Extract individual statuses
    spf_status = auth_results.get("spf", "NONE")
    dkim_status = auth_results.get("dkim", "NONE")
    dmarc_status = auth_results.get("dmarc", "NONE")
    dkim_signed = dkim_sig.get("signed", False)
    
    # Calculate trust score
    trust_score = parser.calculate_trust_score(
        spf_status=spf_status,
        dkim_status=dkim_status,
        dmarc_status=dmarc_status,
        dkim_signed=dkim_signed
    )
    
    # Check if fully verified
    is_verified = parser.is_verified(spf_status, dkim_status, dmarc_status)
    
    return {
        "spf_status": spf_status,
        "dkim_status": dkim_status,
        "dmarc_status": dmarc_status,
        "auth_score": trust_score,
        "is_verified": is_verified,
        "dkim_signed": dkim_signed,
        "auth_headers": auth_data["raw_headers"]
    }
