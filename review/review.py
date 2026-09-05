#!/usr/bin/env python3
"""
Interactive review queue: decide which scraped candidate comments actually
get published to the public site. Nothing reaches data/published.json
without going through this.

Usage:
    python3 review.py
"""
import json
import textwrap
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_PATH = PROJECT_ROOT / "data" / "candidates.json"
PUBLISHED_PATH = PROJECT_ROOT / "site" / "data" / "published.json"

TAGS = ["funny", "heartfelt", "chaotic", "wisdom", "unhinged", "other"]


def load(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save(path, items):
    with path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
        f.write("\n")


def prompt_tag():
    print("Tag: " + ", ".join(f"[{t[0]}]{t[1:]}" for t in TAGS))
    choice = input("  tag > ").strip().lower()
    for t in TAGS:
        if choice == t[0] or choice == t:
            return t
    return "other"


def review_one(candidate):
    print("\n" + "=" * 70)
    print(f"Recipe: {candidate['recipeTitle']}")
    print(f"Author: {candidate['author']}   (+{candidate['recommendedCount']} recommends, "
          f"{candidate['replyCount']} replies)")
    print(f"URL:    {candidate['recipeUrl']}")
    print("-" * 70)
    print(textwrap.fill(candidate["text"], width=70))
    print("=" * 70)
    print("[a]pprove  [e]dit-then-approve  [s]kip  [r]eject-permanently  [q]uit")

    choice = input("> ").strip().lower()
    return choice


def main():
    candidates = load(CANDIDATES_PATH)
    published = load(PUBLISHED_PATH)
    pending = [c for c in candidates if c.get("status", "pending") == "pending"]

    if not pending:
        print("No pending candidates. Run scraper/fetch_comments.py to add more.")
        return

    print(f"{len(pending)} pending candidate(s) to review.\n")

    remaining = []
    quit_early = False

    for candidate in candidates:
        if quit_early or candidate.get("status", "pending") != "pending":
            remaining.append(candidate)
            continue

        choice = review_one(candidate)

        if choice == "a":
            candidate["tag"] = prompt_tag()
            published.append(candidate)
        elif choice == "e":
            print("Current text:")
            print(textwrap.fill(candidate["text"], width=70))
            new_text = input("New text (blank to keep unchanged) > ").strip()
            if new_text:
                candidate["text"] = new_text
            candidate["tag"] = prompt_tag()
            published.append(candidate)
        elif choice == "s":
            remaining.append(candidate)
        elif choice == "r":
            pass  # dropped permanently, not re-added
        elif choice == "q":
            remaining.append(candidate)
            quit_early = True
        else:
            print("Unrecognized choice, skipping.")
            remaining.append(candidate)

    save(CANDIDATES_PATH, remaining)
    save(PUBLISHED_PATH, published)
    print(f"\nPublished total: {len(published)}. Remaining in queue: "
          f"{sum(1 for c in remaining if c.get('status', 'pending') == 'pending')}.")


if __name__ == "__main__":
    main()
