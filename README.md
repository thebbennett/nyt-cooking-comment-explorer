# Read the Comments

A small public site that surfaces a selection of hand-picked comments
on the NYT Cooking website — one of the last corners of the internet where humans interact with each other.

## How it works

1. **Scrape candidates** (`scraper/fetch_comments.py`): fetches a recipe page
   and pulls out the ~15 comments, ranked by reader recommendations. Writes them to `data/candidates.json`, a private review queue. 

2. **Review** (`review/review.py`): an interactive CLI that shows you each
   candidate one at a time. Approve, edit-and-approve, skip, or reject. You
   also tag approved comments (funny / heartfelt / chaotic / wisdom /
   unhinged / other). Only what you approve moves into
   `site/data/published.json`.

3. **The site** (`site/`): a static HTML/CSS/JS page that reads
   `site/data/published.json` and renders it as a searchable, filterable
   gallery. Deploy the `site/` folder anywhere static (Netlify, Vercel, 
   GitHub Pages, S3, etc).

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

