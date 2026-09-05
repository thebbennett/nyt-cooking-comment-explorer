#!/usr/bin/env python3
"""
Manually add a single comment you found while browsing NYT Cooking
yourself -- for the ones the scraper misses because they're not in the
top ~15 "most helpful" comments (e.g. a great reply buried in a thread).

Like the scraper, this only ever writes to data/candidates.json, the
private review queue. It still has to go through review/review.py
before it can appear on the site.

Usage:
    python3 add_comment.py
        Interactive: prompts for the recipe URL, author, and comment text.

    python3 add_comment.py --url <recipe_url> --author "Name" --text "..."
        Non-interactive, for scripting/quick one-liners.
"""
import argparse
import hashlib
import sys
from pathlib import Path

from fetch_comments import (
    CANDIDATES_PATH,
    PUBLISHED_PATH,
    extract_recipe_title,
    fetch_html,
    load_json_list,
    save_json_list,
)


def prompt_multiline(label: str) -> str:
    print(f"{label} (paste the text, then press Enter on an empty line to finish):")
    lines = []
    while True:
        line = input()
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def make_id(recipe_url: str, author: str, text: str) -> str:
    digest = hashlib.sha1(f"{recipe_url}|{author}|{text}".encode("utf-8")).hexdigest()
    return "manual-" + digest[:12]


def build_manual_candidate(recipe_url: str, recipe_title: str, author: str, text: str) -> dict:
    return {
        "id": make_id(recipe_url, author, text),
        "recipeTitle": recipe_title,
        "recipeUrl": recipe_url,
        "author": author or "Anonymous",
        "text": text.strip(),
        "submittedAt": None,
        "recommendedCount": 0,
        "replyCount": 0,
        "status": "pending",
        "source": "manual",
    }


def resolve_title(recipe_url: str, given_title: str | None) -> str:
    if given_title:
        return given_title
    print(f"Fetching recipe title from {recipe_url} ...")
    try:
        html = fetch_html(recipe_url)
        return extract_recipe_title(html)
    except Exception as e:
        print(f"  ! couldn't fetch title automatically ({e})", file=sys.stderr)
        return input("Recipe title (type it yourself) > ").strip() or "Unknown Recipe"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Recipe URL the comment appeared on")
    parser.add_argument("--author", help="Commenter's screen name")
    parser.add_argument("--text", help="The comment text")
    parser.add_argument("--title", help="Recipe title (auto-fetched from --url if omitted)")
    args = parser.parse_args()

    if args.url and args.author and args.text:
        recipe_url, author, text = args.url, args.author, args.text
        title = resolve_title(recipe_url, args.title)
    else:
        print("Add a comment you found manually.\n")
        recipe_url = input("Recipe URL > ").strip()
        author = input("Commenter's name > ").strip()
        text = prompt_multiline("Comment text")
        title = resolve_title(recipe_url, None)

    if not recipe_url or not text:
        print("Need at least a recipe URL and comment text -- aborting.", file=sys.stderr)
        sys.exit(1)

    candidates = load_json_list(CANDIDATES_PATH)
    published = load_json_list(PUBLISHED_PATH)
    known_ids = {c["id"] for c in candidates} | {p["id"] for p in published}

    candidate = build_manual_candidate(recipe_url, title, author, text)

    if candidate["id"] in known_ids:
        print("This exact comment is already in the queue or published -- skipping.")
        return

    candidates.append(candidate)
    save_json_list(CANDIDATES_PATH, candidates)
    print(f"\nAdded to {CANDIDATES_PATH} (recipe: '{title}').")
    print("Run review/review.py when you're ready to review and publish it.")


if __name__ == "__main__":
    main()
