Extract product lines from an RFQ/RFP text.
Focus only on product request data, not company/contact details.

Return JSON only.
Preferred shape:
{
	"products": [
		{
			"quantity": <number|null>,
			"quantity_unit": "<string>",
			"manufacturer": "<string>",
			"part_number": "<string>",
			"description": "<string>"
		}
	]
}

Rules:
- Keep output compact.
- Do not include optional technical attributes.
- If a value is unknown, use null (or "" for quantity_unit).
- Do not add commentary, markdown, or extra keys.
