from __future__ import annotations

import json


def _js_string_literal(value: str) -> str:
    return json.dumps(value)


def build_qa_template(base_url: str) -> str:
    serialized_base_url = _js_string_literal(base_url)
    return f'''import {{ test, expect }} from "@playwright/test";

test("baseline qa", async ({{ page }}) => {{
  await page.goto({serialized_base_url});
  await expect(page).toHaveURL(/.*/);
  await expect(page.locator("body")).toBeVisible();
}});
'''


def build_security_template(base_url: str) -> str:
    serialized_base_url = _js_string_literal(base_url)
    return f'''import {{ test, expect }} from "@playwright/test";

test("baseline security", async ({{ page }}) => {{
  const response = await page.goto({serialized_base_url});
  const headers = response ? response.headers() : {{}};
  expect(headers["strict-transport-security"] || "").not.toBe("");
  await expect(page.locator("text=Exception")).toHaveCount(0);
}});
'''
