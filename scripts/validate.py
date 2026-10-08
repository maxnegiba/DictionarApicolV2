#!/usr/bin/env python3
"""Structural publication gate. Never interprets schema validity as scientific validity."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_KIND = {"TER", "CON", "SOP", "TAX", "PAT", "REG", "DAT", "IMG"}
ALLOWED_STATUS = {"DRAFT", "RESEARCHED", "FACT_CHECKED", "LANGUAGE_REVIEWED", "APPROVED", "BLOCKED", "REJECTED"}
ALLOWED_EDITION = ALLOWED_STATUS - {"REJECTED"}
ALLOWED_RISK = {"P0", "P1", "P2", "P3"}
ID = re.compile(r"^(TER|CON|SOP|TAX|PAT|REG|DAT|IMG)-[0-9]{4,6}$")
errors = []
def fail(where, message): errors.append(f"{where}: {message}")
def load(p):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e: fail(str(p), str(e)); return None

sources_path = ROOT / "data/sources.json"
sources = load(sources_path)
source_ids = set()
if not isinstance(sources, list):
    fail("sources", "must be an array"); sources = []
for s in sources:
    if not isinstance(s, dict) or not s.get("id"):
        fail("sources", "each source needs an id"); continue
    if s["id"] in source_ids: fail("sources", f"duplicate id {s['id']}")
    source_ids.add(s["id"])
seen = set()
for p in sorted((ROOT / "data/records").glob("*.json")):
    r = load(p)
    if not isinstance(r, dict): continue
    rid = r.get("id")
    if not isinstance(rid, str) or not ID.fullmatch(rid): fail(p.name, "invalid id"); continue
    if p.stem != rid: fail(rid, "filename and id differ")
    if rid in seen: fail(rid, "duplicate id")
    seen.add(rid)
    if r.get("kind") not in ALLOWED_KIND or not rid.startswith(r.get("kind", "") + "-"): fail(rid, "invalid kind/id")
    if r.get("status") not in ALLOWED_STATUS: fail(rid, "invalid status")
    if r.get("risk") not in ALLOWED_RISK: fail(rid, "invalid risk")
    modules = r.get("modules")
    if not isinstance(modules, list) or not modules or any(not isinstance(m,str) or not re.fullmatch(r"M(0[1-9]|1[0-2])",m) for m in modules): fail(rid, "invalid modules")
    claims = r.get("claims")
    if not isinstance(claims, list): fail(rid, "claims must be a list"); claims = []
    cids = set()
    for c in claims:
        if not isinstance(c,dict): fail(rid,"claim must be object"); continue
        if not c.get("id") or c["id"] in cids: fail(rid,"missing/duplicate claim id")
        cids.add(c.get("id"))
        if not isinstance(c.get("source_ids"),list): fail(rid, "claim source_ids missing"); continue
        for source_id in c["source_ids"]:
            if source_id not in source_ids: fail(rid,f"unknown source {source_id}")
        if c.get("verification") not in {"UNVERIFIED","SUPPORTED","DISPUTED"}: fail(rid,"invalid claim verification")
    editions = r.get("editions")
    if not isinstance(editions,dict) or set(editions) != {"ro","en"}:
        fail(rid,"both editions ro/en required"); continue
    for lang, ed in editions.items():
        if not isinstance(ed,dict) or ed.get("status") not in ALLOWED_EDITION or not ed.get("title") or not ed.get("body"): fail(rid,f"invalid edition {lang}"); continue
        if ed["status"] == "APPROVED":
            if not ed.get("terminology_reviewed"): fail(rid, f"{lang}: terminology not reviewed")
            if not ed.get("jurisdiction"): fail(rid, f"{lang}: jurisdiction unset")
    if r.get("status") == "APPROVED":
        if any(ed.get("status") != "APPROVED" for ed in editions.values()): fail(rid,"global approval requires both editions")
        if not claims or any(c.get("verification") != "SUPPORTED" or not c.get("source_ids") for c in claims): fail(rid,"approved records need supported, sourced claims")
        if r.get("risk") == "P0" or r.get("kind") in {"PAT","SOP"}:
            review = r.get("external_review", {})
            if not isinstance(review,dict) or review.get("decision") != "APPROVED" or not review.get("reviewer_role") or not review.get("date"): fail(rid, "qualified external review missing")
print(f"Structural validation: {len(seen)} record(s), {len(source_ids)} source(s), {len(errors)} error(s)")
for err in errors: print("ERROR:", err)
sys.exit(1 if errors else 0)
