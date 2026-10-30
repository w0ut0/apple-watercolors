#!/usr/bin/env python3
"""
Scrape apple cultivars from the USDA Pomological Watercolor Collection
mirrored on Wikimedia Commons ("Category:USDA Pomological Watercolors of apples").

Outputs (in --out, default ./data):
  paintings.jsonl      one record per painting (raw + parsed metadata)
  cultivars.json       paintings grouped by cultivar, with a URL-safe slug
  images/<POM id>.<ext> the thumbnail as served by Commons (unmodified)

The script is resumable: already-downloaded images are skipped.

Usage:
  pip install requests
  python scrape_apples.py --width 640 --limit 50
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

API = "https://commons.wikimedia.org/w/api.php"
CATEGORY = "Category:USDA Pomological Watercolors of apples"
# Wikimedia requires a descriptive User-Agent with contact info.
USER_AGENT = "apple-cultivar-scraper/1.0 (project slug generator; contact: wout@olyslagers.be)"

# Categories on each file that are NOT cultivar names.
NON_CULTIVAR_CAT = re.compile(
    r"^(USDA Pomological|Watercolor paintings by|\d{4}-\d{2}-\d{2}$|\d+ \(number\)|"
    r"Extracted images|Diseases|History of|State Fair|Copper|Malus)",
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")


# --------------------------------------------------------------------------- helpers
def strip_html(value: str | None) -> str:
    if not value:
        return ""
    return html.unescape(TAG_RE.sub("", value)).strip()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text


def parse_description(desc: str) -> dict:
    """Parse the fairly regular ImageDescription text.

    e.g. "Image of the York variety of apples (scientific name: Malus domestica),
    with this specimen originating in Richmond, Henrico County, Virginia, United States.
    Source: ..."
    """
    out: dict = {}
    m = re.search(r"Image of (?:the )?(.+?) variet(?:y|ies) of apples?", desc, re.I)
    if m:
        out["cultivar"] = m.group(1).strip()
    m = re.search(r"\(scientific name: ([^)]+)\)", desc, re.I)
    if m:
        out["scientific_name"] = m.group(1).strip()
    m = re.search(r"originating in (.+?)\.(?:\s|$)", desc)
    if m:
        out["origin"] = m.group(1).strip()
    # Short human description: everything before "Source:"
    out["summary"] = desc.split("Source:")[0].strip()
    return out


def cultivar_from_categories(cats: list[str]) -> str | None:
    for c in cats:
        m = re.match(r"^(.+?) \(apple\)$", c, re.I)
        if m:
            return m.group(1).strip()
    return None


# --------------------------------------------------------------------------- API
class Commons:
    def __init__(self, delay: float = 0.5):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.delay = delay

    def get(self, url: str, **kw) -> requests.Response:
        for attempt in range(6):
            r = self.s.get(url, timeout=60, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                wait = int(r.headers.get("Retry-After", 2 ** attempt))
                print(f"  HTTP {r.status_code}, retrying in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        r.raise_for_status()
        return r

    def iter_category_files(self, width: int):
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "generator": "categorymembers",
            "gcmtitle": CATEGORY,
            "gcmtype": "file",
            "gcmlimit": "50",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime",
            "iiurlwidth": str(width),
            "maxlag": "5",
        }
        while True:
            data = self.get(API, params=params).json()
            for page in (data.get("query") or {}).get("pages", []):
                yield page
            if "continue" not in data:
                break
            params.update(data["continue"])
            time.sleep(self.delay)


# --------------------------------------------------------------------------- main
def build_record(page: dict) -> dict | None:
    info = (page.get("imageinfo") or [None])[0]
    if not info:
        return None
    meta = {k: v.get("value") for k, v in (info.get("extmetadata") or {}).items()}
    cats = [c for c in (meta.get("Categories") or "").split("|") if c]
    desc = strip_html(meta.get("ImageDescription"))
    parsed = parse_description(desc)

    cultivar = cultivar_from_categories(cats) or parsed.get("cultivar")
    pom = re.search(r"POM\d{8}", page["title"])
    credit = meta.get("Credit") or ""
    nal = re.search(r'href="([^"]*usdawatercolors[^"]*)"', credit)

    return {
        "pageid": page["pageid"],
        "title": page["title"],
        "pom_id": pom.group(0) if pom else None,
        "cultivar": cultivar,
        "slug": slugify(cultivar) if cultivar else None,
        "scientific_name": parsed.get("scientific_name"),
        "origin": parsed.get("origin"),
        "description": parsed.get("summary") or desc,
        "date": strip_html(meta.get("DateTimeOriginal")) or None,
        "artist": strip_html(meta.get("Artist")) or None,
        "license": meta.get("LicenseShortName"),
        "categories": cats,
        "other_tags": [c for c in cats if not NON_CULTIVAR_CAT.match(c) and not c.lower().endswith("(apple)")],
        "commons_url": info.get("descriptionurl"),
        "usda_url": nal.group(1) if nal else None,
        "original_url": (info.get("url") or "").split("?")[0],
        "original_size": [info.get("width"), info.get("height")],
        "thumb_url": (info.get("thumburl") or "").split("?")[0],
        "thumb_size": [info.get("thumbwidth"), info.get("thumbheight")],
        "mime": info.get("mime"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data", help="output directory")
    ap.add_argument("--width", type=int, default=640, help="requested thumbnail width (px)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N paintings (0 = all)")
    ap.add_argument("--delay", type=float, default=0.3, help="seconds between requests")
    ap.add_argument("--include-unnamed", action="store_true",
                    help="keep paintings without an identifiable cultivar (e.g. disease studies)")
    ap.add_argument("--no-images", action="store_true", help="metadata only")
    args = ap.parse_args()

    out = Path(args.out)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    api = Commons(delay=args.delay)

    records: list[dict] = []
    with open(out / "paintings.jsonl", "w", encoding="utf-8") as fh:
        for page in api.iter_category_files(args.width):
            rec = build_record(page)
            if not rec or (not rec["cultivar"] and not args.include_unnamed):
                continue

            if not args.no_images and rec["thumb_url"]:
                ext = Path(unquote(urlparse(rec["thumb_url"]).path)).suffix.lower() or ".jpg"
                name = f"{rec['pom_id'] or rec['pageid']}{ext}"
                dest = img_dir / name
                if not dest.exists():
                    try:
                        dest.write_bytes(api.get(rec["thumb_url"]).content)
                        time.sleep(args.delay)
                    except requests.RequestException as e:
                        print(f"  ! image failed {rec['title']}: {e}", file=sys.stderr)
                        name = None
                rec["image_file"] = f"images/{name}" if name else None

            records.append(rec)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"[{len(records):>5}] {rec['cultivar'] or '-':<30} {rec['pom_id']}  {rec['origin'] or ''}")
            if args.limit and len(records) >= args.limit:
                break

    # Group by cultivar -> one entry per slug
    cultivars: dict[str, dict] = {}
    for r in records:
        if not r["slug"]:
            continue
        c = cultivars.setdefault(r["slug"], {
            "slug": r["slug"],
            "name": r["cultivar"],
            "scientific_name": r["scientific_name"],
            "origins": [],
            "artists": [],
            "paintings": [],
        })
        for key, field in (("origins", "origin"), ("artists", "artist")):
            if r[field] and r[field] not in c[key]:
                c[key].append(r[field])
        c["paintings"].append({k: r.get(k) for k in (
            "pom_id", "date", "description", "image_file", "thumb_url",
            "original_url", "commons_url", "usda_url", "license")})

    result = sorted(cultivars.values(), key=lambda c: c["slug"])
    (out / "cultivars.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone: {len(records)} paintings, {len(result)} cultivars -> {out.resolve()}")


if __name__ == "__main__":
    main()
