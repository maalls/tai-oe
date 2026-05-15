from html.parser import HTMLParser


class EmailHTMLParser(HTMLParser):
    """Parse HTML and extract visible text, skipping style/script/head blocks."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_content = False
        self.skip_tags = {"style", "script", "head"}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip_content = True

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip_content = False

    def handle_data(self, data):
        if not self.skip_content:
            self.text.append(data)

    def get_text(self):
        return "".join(self.text)


class Parser(EmailHTMLParser):
    """Backwards-compatible alias used by legacy business handlers."""

