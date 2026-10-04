#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import json
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
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"duplicate id: {attrs['id']}"
            self.ids.add(attrs["id"])
            if tag in {"input", "select", "textarea"}:
                self.inputs[attrs["id"]] = attrs


for path in ROOT.rglob("*.html"):
    parser = Document()
    parser.feed(path.read_text())
    parser.close()

home_doc, ebp_doc, eba_doc = Document(), Document(), Document()
for parser, page in ((home_doc, HOME), (ebp_doc, EBP), (eba_doc, EBA)):
    parser.feed(page)
    parser.close()

assert '<title>Contract Breakpoint | Pre-Signature Contract Analysis</title>' in HOME
seo_description = "Pre-signature analysis of one execution-sensitive commercial agreement to identify where operational conditions can break contractual protection before signature."
assert HOME.count(seo_description) >= 4
assert "€12,000" not in HOME and "&euro;12,000" not in HOME
assert "Fixed fee" not in re.search(r'<section class="hero">(.*?)</section>', HOME, re.S).group(1)
assert "Check whether the agreement fits" in HOME
assert "MATERIAL EXECUTION EXPOSURE" in HOME
assert "EXECUTION-SENSITIVE</div>" not in HOME and "MATERIAL EXPOSURE</div>" not in HOME
assert "Contractual protection can depend on information, timing and notice working in the same operational sequence." in HOME
assert HOME.count('href="/execution-breakpoint-protection/"') == 2
assert "WHAT A BREAKPOINT LOOKS LIKE" in HOME
assert "WHO WRITES THE ANALYSIS" in HOME
for publisher in ("Ship &amp; Bunker", "Trade Finance Global", "Container News"):
    assert publisher in HOME
assert HOME.count('target="_blank" rel="noopener noreferrer"') >= 5
assert "ETInfra" not in HOME and "Substack" not in HOME and 'href="/media/' not in HOME
assert 'href="#fees"' not in HOME
assert set(home_doc.inputs) == {"name", "company", "email", "context"}
assert "required" not in home_doc.inputs["name"]
assert all("required" in home_doc.inputs[field] for field in ("company", "email", "context"))
assert "providerConfirmedSuccess(response,data)" in HOME
assert "cba-error" in HOME and "cba-success" in HOME
assert "product:'Contract Breakpoint'" in HOME
assert "name:value('name')||'Website enquiry'" in HOME
assert "#cep" in HOME and "window.location.replace('/execution-breakpoint-protection/')" in HOME

assert "Execution Breakpoint Protection" in EBP
assert "€2,500 monthly retainer" in EBP
for term in ("One signed contract", "No minimum term", "Cancelable", "No tiers", "No bundles", "No setup fee"):
    assert term in EBP
assert "WHAT YOU RECEIVE" in EBP
assert set(ebp_doc.inputs) == {"ebp-name", "ebp-email", "ebp-company", "ebp-exposure", "ebp-deadline", "ebp-context"}
for option in ("Notice", "Timing", "Escalation", "Recipient", "Format", "Not sure"):
    assert f"<option>{option}</option>" in EBP
assert "product:'EBP'" in EBP and "subject:'[EBP REQUEST]'" in EBP
assert "providerConfirmedSuccess(response,result)" in EBP
assert EBP.count('href="https://contractbreakpoint.com/"') == 1
for removed_link in ('href="/about/"', 'href="/notes/"', 'href="/signals/"'):
    assert removed_link not in EBP
assert "earnings-breakpoint-analysis" not in EBP.lower()

assert "Earnings Breakpoint Analysis" in EBA
assert "PREPARED BY" in EBA and "former Loading Master with 25+ years" in EBA
assert "Single-name read from USD 4,000" in EBA and "Facility / portfolio read from USD 12,000" in EBA
assert set(eba_doc.inputs) == {"eba-organisation", "eba-email", "eba-role", "eba-use-case", "eba-assessment", "eba-context"}
for option in ("Pre-deal", "Watchlist", "Single name", "Facility / portfolio"):
    assert f"<option>{option}</option>" in EBA
assert "product:'EBA'" in EBA and "subject:'[EBA REQUEST]'" in EBA
assert "response.ok===true" in EBA and "data.success===true" in EBA
assert 'href="/"' not in EBA and "execution-breakpoint-protection" not in EBA.lower()
assert "Published Analysis" not in EBA
assert "/notes/" not in eba_doc.links and "/signals/" not in eba_doc.links
for removed_copy in ("operator-side", "before the deterioration appears in the DSCR", "Maritime credit covers the iron and the paper. Rarely the charter.", "Priced against the exposure, not the hours.", "hugo@contractbreakpoint.com"):
    assert removed_copy not in EBA
assert "LENDER-SIDE STRUCTURAL EXECUTION ANALYSIS" in EBA
assert "EBA assesses structural exposure, not probability." in EBA
assert "hugofhernandez@protonmail.com" in EBA

assert transport_config(HOME)["access_key"] == "5986f283-7f45-4503-8eba-f1c5bb0a7096"
assert transport_config(EBP)["access_key"] == "5986f283-7f45-4503-8eba-f1c5bb0a7096"
assert transport_config(EBA)["access_key"] == "8a32b785-51c0-4147-a3ad-5b92441589ff"
for page in (HOME, EBP, EBA):
    config = transport_config(page)
    assert config["endpoint"] == "https://api.web3forms.com/submit"
    assert config["method"] == "POST" and config["content_type"] == "application/json"
    assert config["serialization"] and config["reply_to"]
assert provider_confirmed_success(True, {"success": False}) is False
assert provider_confirmed_success(True, {"success": True}) is True
assert provider_confirmed_success(False, {"success": True}) is False

schema = json.loads(re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', HOME, re.S).group(1))
assert "12,000" not in json.dumps(schema)

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

assert not (ROOT / "media").exists()
print("release validation passed")
