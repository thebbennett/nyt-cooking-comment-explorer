# Read the Comments

A small public site that surfaces the funniest, weirdest, most human comments
left on NYT Cooking recipes — one of the last corners of the internet where
strangers still argue, commiserate, and crack jokes at each other in good faith.

## How it works

Three stages, with a human in the loop before anything goes public:

1. **Scrape candidates** (`scraper/fetch_comments.py`) — fetches a recipe page
   (the same HTML a browser would load) and pulls out the ~15 comments NYT
   already embeds server-side, ranked by reader recommendations. Writes them
   to `data/candidates.json`, a private review queue. Nothing here is public.

2. **Review** (`review/review.py`) — an interactive CLI that shows you each
   candidate one at a time. Approve, edit-and-approve, skip, or reject. You
   also tag approved comments (funny / heartfelt / chaotic / wisdom /
   unhinged / other). Only what you approve moves into
   `site/data/published.json`.

3. **The site** (`site/`) — a static HTML/CSS/JS page that reads
   `site/data/published.json` and renders it as a searchable, filterable
   gallery. No backend, no build step — deploy the `site/` folder anywhere
   static (Netlify, Vercel, GitHub Pages, S3, etc).

## Why it's built this way

- **Only reviewed content is deployable.** `data/candidates.json` (raw,
  unreviewed scrape output) lives *outside* `site/`, and is git-ignored, so
  it can never accidentally end up in the public deploy or a public repo.
  Only `site/data/published.json` — the stuff you've actually looked at and
  approved — is ever served.
- **Attribution + link-back on everything.** Every published comment keeps
  the commenter's NYT screen name and links back to the original recipe.
  This is meant to read as curation/commentary (like quoting a good tweet),
  not as a full republish of NYT's comment section.
- **A takedown path exists.** The site footer has a contact email for anyone
  who wants their comment removed.
- **Scraping is deliberately slow and small-scale.** The fetcher processes
  one recipe URL at a time with a multi-second delay between requests —
  there's no reason to hit NYT's servers any harder than a human clicking
  through recipes would.

Worth knowing: NYT Cooking's Terms of Service likely restrict automated
scraping even at this small scale, and this hasn't been reviewed by a lawyer.
The design choices above (manual review gate, attribution, link-back,
takedown contact, low volume) are meant to keep this closer to fair-use
commentary than to republishing — but that's a risk-reduction posture, not
a guarantee. If you ever want to scale this up significantly or monetize
it, that's the point to actually get legal advice.

## Usage

```bash
cd scraper
python3 fetch_comments.py https://cooking.nytimes.com/recipes/1015819-chocolate-chip-cookies
# or, from a list:
python3 fetch_comments.py --file recipe_urls.txt
```

Then review what came in:

```bash
cd review
python3 review.py
```

Then preview the site locally:

```bash
cd site
python3 -m http.server 8000
# open http://localhost:8000
```

## Note on the "top comments" heuristic

The scraper pulls the comments NYT ranks as most-recommended, which skews
toward *useful* tips (metric conversions, substitution advice) rather than
*funny* ones. For genuine comedy, you'll likely do better hand-picking
recipes you already know have a great comment section (controversial
recipes, divisive ingredients, anything that went viral) and feeding those
URLs to the scraper, rather than scraping at random.

## Seed data

`site/data/published.json` currently ships with 3 real (scraped, attributed,
link-backed) example comments from a chocolate chip cookie recipe, just so
the site isn't empty on first run. Replace them via the normal
scrape → review → publish flow whenever you're ready.
