"""md_to_pdf.py — Convert markdown to PDF using markdown + Playwright."""
import os
import markdown
from playwright.sync_api import sync_playwright


def md_to_pdf(md_path, pdf_path):
    with open(md_path, encoding="utf-8") as f:
        md_content = f.read()

    html = markdown.markdown(
        md_content, extensions=["tables", "fenced_code", "toc", "nl2br"]
    )

    full_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
    body {{ font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; font-size: 14px; line-height: 1.6; color: #1a1a1a; }}
    h1 {{ font-size: 24px; border-bottom: 2px solid #333; padding-bottom: 8px; }}
    h2 {{ font-size: 20px; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 6px; }}
    h3 {{ font-size: 16px; margin-top: 24px; }}
    h4 {{ font-size: 14px; margin-top: 20px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f5f5f5; font-weight: 600; }}
    code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }}
    pre {{ background: #f5f5f5; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 13px; }}
    pre code {{ background: none; padding: 0; }}
    blockquote {{ border-left: 3px solid #ddd; margin: 16px 0; padding: 8px 16px; color: #555; }}
    strong {{ font-weight: 700; }}
    ul, ol {{ padding-left: 24px; }}
    li {{ margin-bottom: 4px; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 24px 0; }}
</style>
</head><body>{html}</body></html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full_html, wait_until="networkidle")
        page.pdf(
            path=pdf_path,
            format="A4",
            margin={
                "top": "20mm",
                "bottom": "20mm",
                "left": "20mm",
                "right": "20mm",
            },
        )
        browser.close()


if __name__ == "__main__":
    BASE = os.path.dirname(os.path.abspath(__file__))
    exports = os.path.join(BASE, "exports")
    os.makedirs(exports, exist_ok=True)

    files = [
        ("GLANCE_Mathematics.md", "GLANCE_Mathematics.pdf"),
        ("GLANCE_Paper_Draft.md", "GLANCE_Paper_Draft.pdf"),
        ("SciSense_Business_Plan.md", "SciSense_Business_Plan.pdf"),
    ]
    for md, pdf in files:
        md_path = os.path.join(BASE, md)
        pdf_path = os.path.join(exports, pdf)
        if os.path.exists(md_path):
            print(f"Converting {md} -> {pdf}...")
            md_to_pdf(md_path, pdf_path)
            size_kb = os.path.getsize(pdf_path) // 1024
            print(f"  Done: {size_kb} KB")
        else:
            print(f"  SKIP: {md} not found")
