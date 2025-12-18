#!/usr/bin/env python3
import json
import re
from pathlib import Path

BIB_FILES = [
    Path("bib/publications.bib"),
    Path("bib/working_papers.bib"),
]
OUT_JSON = Path("site/publications.json")

ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,]+)\s*,(.*?)\n\}", re.S)
FIELD_RE = re.compile(
    r"^\s*(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\".*?\"|[^,\n]+)\s*,?\s*$",
    re.M
)


def strip_wrapping(v: str) -> str:
    v = (v or "").strip()
    if (v.startswith("{") and v.endswith("}")) or (v.startswith('"') and v.endswith('"')):
        v = v[1:-1]
    return v

def clean_tex(v: str) -> str:
    v = strip_wrapping(v)
    v = v.replace("{", "").replace("}", "")
    v = v.replace(r"\&", "&")
    v = re.sub(r"\s+", " ", v).strip()
    return v

def split_tags(v: str) -> list[str]:
    v = clean_tex(v)
    if not v:
        return []
    return [x.strip() for x in v.split(",") if x.strip()]

def fix_doi_url(raw: str) -> str:
    """
    Accepts:
      - https://doi.org/10....
      - 10....
      - https://10....   (your broken case)
    Returns a proper https://doi.org/10.... URL.
    """
    s = clean_tex(raw)
    if not s:
        return ""

    s = s.replace("http://doi.org/", "https://doi.org/").replace("https://doi.org/", "https://doi.org/")

    # If it already is a doi.org URL, keep it.
    if s.startswith("https://doi.org/"):
        return s

    # If it starts with https://10.... or http://10...., strip scheme.
    s = re.sub(r"^https?://", "", s)

    # If it now looks like a DOI (starts with 10.), convert to doi.org.
    if s.startswith("10."):
        return f"https://doi.org/{s}"

    # Otherwise, leave as-is (could be a URL field)
    return s

def pick_date(fields: dict) -> str:
    d = clean_tex(fields.get("date", ""))
    if d:
        return d
    y = clean_tex(fields.get("year", ""))
    return f"{y}-01-01" if y else ""

def pick_year(fields: dict) -> str:
    y = clean_tex(fields.get("year", ""))
    if y:
        return y
    d = clean_tex(fields.get("date", ""))
    return d[:4] if len(d) >= 4 else ""

def pick_venue(fields: dict) -> str:
    return clean_tex(
        fields.get("journaltitle")
        or fields.get("journal")
        or fields.get("booktitle")
        or fields.get("publisher")
        or ""
    )

def parse_authors(fields: dict) -> list[str]:
    a = clean_tex(fields.get("author", ""))
    if not a:
        return []
    return [p.strip() for p in a.split(" and ") if p.strip()]

def parse_fields(body: str) -> dict[str, str]:
    # Split "key = value, key2 = value2, ..." safely (commas inside braces are ignored)
    parts = []
    buf = []
    depth = 0
    in_quotes = False

    for ch in body:
        if ch == '"' and depth == 0:
            in_quotes = not in_quotes
        elif ch == "{" and not in_quotes:
            depth += 1
        elif ch == "}" and not in_quotes and depth > 0:
            depth -= 1

        if ch == "," and depth == 0 and not in_quotes:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)

    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)

    fields: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        fields[k.strip().lower()] = v.strip()
    return fields


def parse_bibtex(text: str) -> list[dict]:
    out = []
    for m in ENTRY_RE.finditer(text):
        entrytype, entryid, body = m.group(1).lower(), m.group(2).strip(), m.group(3)

        fields = parse_fields(body)

        title = clean_tex(fields.get("title", ""))
        if not title:
            continue

        tags = split_tags(fields.get("keywords", "")) or split_tags(fields.get("themes", ""))

        item = {
            "id": entryid,
            "type": entrytype,
            "title": title,
            "authors": parse_authors(fields),
            "venue": pick_venue(fields),
            "year": pick_year(fields),
            "date": pick_date(fields),
            "doi_url": fix_doi_url(fields.get("doi", "") or fields.get("doi_url", "")),
            "note": clean_tex(fields.get("note", "") or fields.get("pubstate", "")),
            "keywords": tags,
        }
        out.append(item)

    return out


def main() -> None:
    items: list[dict] = []
    for f in BIB_FILES:
        if f.exists():
            items.extend(parse_bibtex(f.read_text(encoding="utf-8", errors="ignore")))

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Wrote {OUT_JSON} with {len(items)} items")

if __name__ == "__main__":
    main()
