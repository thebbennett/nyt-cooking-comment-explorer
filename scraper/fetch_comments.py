#!/usr/bin/env python3
"""
Fetch candidate comments from NYT Cooking recipe pages for manual review.

NYT Cooking embeds its ~15 most-recommended comments directly in each
recipe page's HTML (the same page a browser would load). This script
fetches that page once per URL -- same as a human visit -- extracts the
embedded comment JSON, and appends anything new to data/candidates.json
as a review queue. Nothing here is published automatically; a human
(review/review.py) decides what actually goes on the site.

Usage:
    python3 fetch_comments.py <recipe_url> [<recipe_url> ...]
    python3 fetch_comments.py --file recipe_urls.txt

Be polite: this defaults to a multi-second delay between requests and
processes one page at a time. Don't remove the delay or parallelize
requests -- there's no reason to hammer NYT's servers for a personal
curation project.
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_PATH = PROJECT_ROOT / "data" / "candidates.json"
PUBLISHED_PATH = PROJECT_ROOT / "site" / "data" / "published.json"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

HELPFUL_NOTES_RE = re.compile(r'"helpfulNotes":"((?:\\.|[^"\\])*)"')
TITLE_RE = re.compile(r"<title[^>]*>([^<]*)</title>")


def load_json_list(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json_list(path: Path, items: list) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_recipe_title(html: str) -> str:
    m = TITLE_RE.search(html)
    if not m:
        return "Unknown Recipe"
    title = m.group(1).strip()
    # NYT titles look like "Best Chocolate Chip Cookies Recipe"
    if title.endswith(" Recipe"):
        title = title[: -len(" Recipe")]
    return title


def extract_comments(html: str) -> list:
    m = HELPFUL_NOTES_RE.search(html)
    if not m:
        return []
    inner_json_string = json.loads('"' + m.group(1) + '"')
    data = json.loads(inner_json_string)
    return data.get("notes", [])


def strip_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


def build_candidate(note: dict, recipe_title: str, recipe_url: str) -> dict:
    return {
        "id": note["id"],
        "recipeTitle": recipe_title,
        "recipeUrl": recipe_url,
        "author": note.get("author", {}).get("name", "Anonymous"),
        "text": strip_html_tags(note.get("text", "")),
        "submittedAt": note.get("submittedAt"),
        "recommendedCount": note.get("recommendedCount", 0),
        "replyCount": note.get("replyCount", 0),
        "status": "pending",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", help="Recipe URLs to scan")
    parser.add_argument("--file", help="Path to a text file of recipe URLs, one per line")
    parser.add_argument(
        "--delay", type=float, default=3.0, help="Seconds to wait between requests (default 3.0)"
    )
    args = parser.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            urls.extend(
                line.strip() for line in f if line.strip() and not line.startswith("#")
            )

    if not urls:
        parser.error("Provide one or more recipe URLs, or --file recipe_urls.txt")

    candidates = load_json_list(CANDIDATES_PATH)
    published = load_json_list(PUBLISHED_PATH)
    known_ids = {c["id"] for c in candidates} | {p["id"] for p in published}

    added = 0
    for i, url in enumerate(urls):
        print(f"[{i + 1}/{len(urls)}] Fetching {url}")
        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"  ! failed to fetch: {e}", file=sys.stderr)
            continue

        title = extract_recipe_title(html)
        notes = extract_comments(html)
        print(f"  found {len(notes)} embedded comments on '{title}'")

        for note in notes:
            if note["id"] in known_ids:
                continue
            candidates.append(build_candidate(note, title, url))
            known_ids.add(note["id"])
            added += 1

        if i < len(urls) - 1:
            time.sleep(args.delay)

    save_json_list(CANDIDATES_PATH, candidates)
    print(f"\nAdded {added} new candidate comment(s) to {CANDIDATES_PATH}")
    print("Run review/review.py to review and publish them.")


if __name__ == "__main__":
    main()
