"""Email classification helper backed by an LLM client."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.llm import LLMClient
from src.controller.llm_factory import LLMClientFactory


class EmailClassifier:
	"""Classify emails using a provided LLM client."""

	def __init__(
		self,
	) -> None:
		factory = LLMClientFactory()
		self.client = factory.create_client()
		# Load system prompt from file
		prompt_path = Path(__file__).parent / "prompt.md"
		self.system_prompt = prompt_path.read_text().strip()

	def classify(self, title: str, body: str, from_email: Optional[str] = None) -> Dict[str, Optional[str]]:
		"""Classify the email contents.

		Parameters
		----------
		title: str
			Email subject line.
		from_email: Optional[str]
			Sender email address.
		body: str
			Email body text.
		"""

		print("classfiying email")
		user_content = f"From: {from_email or 'Unknown'}\nSubject: {title}\n\nBody:\n{body}"

		response = self.client.ask_json(
			system_prompt=self.system_prompt,
			user_content=user_content,
			temperature=0.0,
			max_tokens=200,
		)

		print(f"[EmailClassifier] LLM response: {json.dumps(response)}")

		return response
