import unittest

from response_formatting import format_ai_content


class ResponseFormattingTests(unittest.TestCase):
    def test_renders_headings_paragraphs_and_points_without_break_tags(self):
        rendered = format_ai_content(
            "**कार्य पर ध्यान दें**\n"
            "वर्तमान क्षण में अपना सर्वश्रेष्ठ दें।\n"
            "- कार्यों को छोटे चरणों में बाँटें।\n"
            "- स्पष्ट इरादा तय करें।\n\n"
            "**चिंतन**\n"
            "मैं अभी क्या कर रहा हूँ?"
        )

        self.assertIn("<h3>कार्य पर ध्यान दें</h3>", rendered)
        self.assertIn("<p>वर्तमान क्षण में अपना सर्वश्रेष्ठ दें।</p>", rendered)
        self.assertIn("<li>कार्यों को छोटे चरणों में बाँटें।</li>", rendered)
        self.assertIn("<h3>चिंतन</h3>", rendered)
        self.assertNotIn("<br", rendered.lower())

    def test_converts_markdown_table_rows_to_headings_and_bullets(self):
        rendered = format_ai_content(
            "| तरीका | लाभ | अभ्यास |\n"
            "|---|---|---|\n"
            "| समत्व बनाए रखें | मन शांत रहता है | • साँस लें<br>• साँस छोड़ें |"
        )

        self.assertIn("<h4>समत्व बनाए रखें</h4>", rendered)
        self.assertIn("<strong>लाभ:</strong>", rendered)
        self.assertIn("<strong>अभ्यास:</strong>", rendered)
        self.assertIn("<li>साँस लें</li>", rendered)
        self.assertIn("<li>साँस छोड़ें</li>", rendered)
        self.assertNotIn("<br", rendered.lower())
        self.assertNotIn("<table", rendered.lower())

    def test_keeps_numbered_list_items_together_across_blank_lines(self):
        rendered = format_ai_content(
            "1. List your strongest skills.\n\n"
            "1. Identify skills that align with the roles you’re considering.\n\n"
            "1. Spot any gaps.\n\n"
            "Once you have that list, you can:"
        )

        self.assertEqual(rendered.count("<ol>"), 1)
        self.assertEqual(rendered.count("</ol>"), 1)
        self.assertEqual(rendered.count("<li>"), 3)
        self.assertIn("<p>Once you have that list, you can:</p>", rendered)

    def test_escapes_untrusted_html(self):
        rendered = format_ai_content("**सुरक्षित**\n<script>alert(1)</script>")

        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)


if __name__ == "__main__":
    unittest.main()
