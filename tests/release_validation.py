#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "index.html").read_text()
EBP = (ROOT / "execution-breakpoint-protection/index.html").read_text()
EBA = (ROOT / "earnings-breakpoint-analysis/index.html").read_text()


def transport_config(page):
    return {
        "endpoint": re.search(r"fetch\('([^']+)'", page).group(1),
        "access_key": re.search(r"access_key:\s*'([^']+)'", page).group(1),
        "method": re.search(r"method:'([^']+)'", page).group(1),
        "content_type": re.search(r"'Content-Type':'([^']+)'", page).group(1),
        "serialization": "JSON.stringify(payload)" in page,
        "reply_to": "email:value(" in page,
    }


def provider_confirmed_success(response_ok, data):
    return response_ok is True and data is not None and data.get("success") is True


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

assert HOME.count('href="/execution-breakpoint-protection/"') == 2
signed_fields = re.search(r'<div id="signed-fields" style="display:none;">(.*?)</div>\s*</div>', HOME, re.S).group(1)
assert "not eligible for Contract Breakpoint Analysis" in signed_fields
assert '<a href="/execution-breakpoint-protection/">Continue with Execution Breakpoint Protection &rarr;</a>' in signed_fields
assert "signedFields.style.display = 'none'" in HOME
assert "signedFields.style.display = 'block'" in HOME
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
assert "from USD 4,000" in EBA and "from USD 5,000" not in EBA
assert "from USD 12,000" in EBA
assert "product:'EBA'" in EBA and "subject:'[EBA REQUEST]'" in EBA
assert "response.ok===true" in EBA and "data.success===true" in EBA
assert transport_config(HOME)["access_key"] == "5986f283-7f45-4503-8eba-f1c5bb0a7096"
assert transport_config(EBP)["access_key"] == "5986f283-7f45-4503-8eba-f1c5bb0a7096"
assert transport_config(EBA)["access_key"] == "f3a32095-bde6-4618-bf09-e72ec897933c"
for field in ("endpoint", "method", "content_type", "serialization", "reply_to"):
    assert transport_config(EBA)[field] == transport_config(EBP)[field]
assert provider_confirmed_success(True, {"success": False}) is False
assert provider_confirmed_success(True, {"success": True}) is True
assert provider_confirmed_success(False, {"success": True}) is False
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
