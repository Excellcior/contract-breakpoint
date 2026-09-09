#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "index.html").read_text()
EBP = (ROOT / "execution-breakpoint-protection/index.html").read_text()
EBA = (ROOT / "earnings-breakpoint-analysis/index.html").read_text()


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"duplicate id: {attrs['id']}"
            self.ids.add(attrs["id"])


for path in ROOT.rglob("*.html"):
    parser = Document()
    parser.feed(path.read_text())
    parser.close()

assert HOME.count('href="/execution-breakpoint-protection/"') == 1
assert 'href="/earnings-breakpoint-analysis/"' not in HOME
assert "€12,000" in HOME and "product: 'CBA'" in HOME
assert "#cep" in HOME and "window.location.replace('/execution-breakpoint-protection/')" in HOME

assert "Execution Breakpoint Protection" in EBP
assert "€2,500 monthly retainer" in EBP
assert "No minimum term" in EBP and "Cancelable" in EBP
assert "product:'EBP'" in EBP and "subject:'[EBP REQUEST]'" in EBP
assert EBP.count('href="/"') == 1
assert "earnings-breakpoint-analysis" not in EBP.lower()

assert "Earnings Breakpoint Analysis" in EBA
assert "does not predict whether" in EBA
assert "from USD 5,000" in EBA and "from USD 12,000" in EBA
assert "product:'EBA'" in EBA and "subject:'[EBA REQUEST]'" in EBA
assert 'href="/"' not in EBA and "execution-breakpoint-protection" not in EBA.lower()
for phrase in (
    "whether the charter will perform",
    "will the charterer pay",
    "expected charterer behaviour",
    "likelihood of default",
    "probability of payment",
):
    assert phrase not in EBA.lower(), phrase

tree = ET.parse(ROOT / "sitemap.xml")
locations = {item.text for item in tree.findall(".//{*}loc")}
assert "https://contractbreakpoint.com/execution-breakpoint-protection/" in locations
assert "https://contractbreakpoint.com/earnings-breakpoint-analysis/" in locations

eba_path = "/earnings-breakpoint-analysis/"
for path in ROOT.rglob("*.html"):
    if path == ROOT / "earnings-breakpoint-analysis/index.html":
        continue
    document = Document()
    document.feed(path.read_text())
    assert eba_path not in document.links, f"unauthorized EBA link: {path}"

redirects = (ROOT / "_redirects").read_text().splitlines()
for source in ("/contract-execution-protection", "/contract-execution-protection/", "/cep", "/cep/"):
    assert f"{source} /execution-breakpoint-protection/ 301" in redirects

for page, canonical, title, description in (
    (EBP, "https://contractbreakpoint.com/execution-breakpoint-protection/", "Execution Breakpoint Protection | Post-Signature Procedural Protection", "Written post-signature procedural protection"),
    (EBA, "https://contractbreakpoint.com/earnings-breakpoint-analysis/", "Earnings Breakpoint Analysis | Structural Hire Cash-Flow Read for Maritime Lenders", "A written operator-side assessment"),
):
    assert f'<link rel="canonical" href="{canonical}"' in page
    assert f"<title>{title}</title>" in page
    assert description in page
    assert "noindex" not in page.lower()

print("release validation passed")
