import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tag.verification.playwright_templates import build_qa_template, build_security_template


class TagPlaywrightTemplateTests(unittest.TestCase):
    def test_templates_include_expected_browser_checks(self) -> None:
        qa = build_qa_template("https://example.test")
        security = build_security_template("https://example.test")
        self.assertIn("page.goto", qa)
        self.assertIn("expect(page)", qa)
        self.assertIn("response", security)
        self.assertIn("strict-transport-security", security.lower())

    def test_templates_escape_quote_containing_urls(self) -> None:
        base_url = 'https://example.test/path?value="quoted"&mode=test'
        qa = build_qa_template(base_url)
        security = build_security_template(base_url)
        self.assertIn('"https://example.test/path?value=\\\"quoted\\\"&mode=test"', qa)
        self.assertIn('"https://example.test/path?value=\\\"quoted\\\"&mode=test"', security)
        self.assertNotIn('page.goto("https://example.test/path?value="quoted"&mode=test")', qa)
        self.assertNotIn('page.goto("https://example.test/path?value="quoted"&mode=test")', security)


if __name__ == "__main__":
    unittest.main()
