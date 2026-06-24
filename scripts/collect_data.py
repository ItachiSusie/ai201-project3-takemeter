"""
collect_data.py — Collect r/nba posts from Reddit RSS feeds.

Usage:
    python scripts/collect_data.py

Outputs:
    data/raw_posts.csv       All collected posts (text + url)
    data/nba_dataset.csv     Auto-labeled dataset ready for review

Auto-labeling uses keyword heuristics as a FIRST PASS only.
All labels must be manually reviewed before training.
"""

import requests
import xml.etree.ElementTree as ET
import csv
import re
import time
import html
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────

RSS_FEEDS = [
    "https://www.reddit.com/r/nba/hot.json",      # covered via RSS below
    "https://www.reddit.com/r/nba/.rss",
    "https://www.reddit.com/r/nba/new/.rss",
    "https://www.reddit.com/r/nba/controversial/.rss",
    "https://www.reddit.com/r/nba/top/.rss?t=week",
    "https://www.reddit.com/r/nba/top/.rss?t=month",
    "https://www.reddit.com/r/nba/top/.rss?t=year",
]

HEADERS = {"User-Agent": "TakeMeter/1.0 academic project"}
NS = {"atom": "http://www.w3.org/2005/Atom"}

# ── Heuristic labeling rules ────────────────────────────────────────────────

REACTION_PATTERNS = [
    r"\b(tonight|right now|this game|that play|just happened|omg|omfg|lmao|lmfao|wtf|holy|wow|insane|crazy)\b",
    r"\b(game thread|post game|live|half time|q[1-4]|ot)\b",
    r"[!]{2,}",           # multiple exclamation marks
    r"\b[A-Z]{4,}\b",     # all-caps words (OMFG, LAKERS, etc.)
    r"^.{0,60}[!?]+$",    # short posts ending in ! or ?
]

HOT_TAKE_PATTERNS = [
    r"\b(overrated|underrated|most overrated|best ever|worst ever|goat|not the goat|fraud|soft|weak|crybaby|excuses?)\b",
    r"\b(jordan would|lebron would|could never|always has been|always will be|unpopular opinion|change my mind|fight me)\b",
    r"\b(nobody talks about|everyone ignores|the truth is|let's be honest|hot take|actually|in reality)\b",
    r"\b(era hopping|era adjusted|load management|scared|afraid to compete)\b",
]

ANALYSIS_PATTERNS = [
    r"\d+\.?\d*\s*%",                       # percentages
    r"\b\d+\s*/\s*\d+\b",                   # fractions like 6/8
    r"\bper 100|per game|per 36|ts%|efg%|fg%|3p%|ft%|win share|bpm|vorp|rapm|raptor\b",
    r"\b(historically|compared to|relative to|in context|breakdown|deeper look|data shows|evidence)\b",
    r"\b(scheme|system|matchup|spacing|switch|hedge|drop|zone|iso|pick and roll|p&r)\b",
    r"\b(since \d{4}|in the last \d+ years?|over the past|dating back to)\b",
]


def strip_html(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def score_label(text: str) -> tuple[str, float]:
    """
    Return (label, confidence) using heuristic pattern matching.
    confidence is a rough count of matched patterns.
    """
    text_lower = text.lower()

    reaction_hits = sum(
        1 for p in REACTION_PATTERNS if re.search(p, text_lower, re.IGNORECASE)
    )
    hot_take_hits = sum(
        1 for p in HOT_TAKE_PATTERNS if re.search(p, text_lower, re.IGNORECASE)
    )
    analysis_hits = sum(
        1 for p in ANALYSIS_PATTERNS if re.search(p, text_lower, re.IGNORECASE)
    )

    scores = {
        "reaction": reaction_hits,
        "hot_take": hot_take_hits,
        "analysis": analysis_hits,
    }
    top_label = max(scores, key=scores.get)
    top_score = scores[top_label]

    # If all tied at 0, default to hot_take (most common in general discussion)
    if top_score == 0:
        return "hot_take", 0.0

    total = sum(scores.values()) or 1
    confidence = round(top_score / total, 2)
    return top_label, confidence


def fetch_rss(url: str) -> list[dict]:
    """Fetch an RSS feed and return a list of post dicts."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  [SKIP] {url} -> HTTP {r.status_code}")
            return []
        root = ET.fromstring(r.text)
        entries = root.findall("atom:entry", NS)
        posts = []
        for entry in entries:
            title_el = entry.find("atom:title", NS)
            content_el = entry.find("atom:content", NS)
            link_el = entry.find("atom:link", NS)
            author_el = entry.find("atom:author/atom:name", NS)

            title = title_el.text if title_el is not None else ""
            raw_content = (content_el.text or "") if content_el is not None else ""
            url_val = link_el.attrib.get("href", "") if link_el is not None else ""

            # Strip HTML from content, extract meaningful text
            clean_content = strip_html(raw_content)

            # Skip bot/meta posts
            if any(
                kw in title.lower()
                for kw in ["[game thread]", "[post game thread]", "[weekly thread]",
                           "[daily thread]", "[mod post]", "r/nba"]
            ):
                continue

            # Use title as primary text; append self-text body if available and not link-only
            text = title.strip()
            # Extract self-post body (appears after "submitted by" block)
            body_match = re.search(r"(?:submitted by.*?\n)([\s\S]+?)(?:\n\d+ comment|$)", clean_content)
            if body_match:
                body = body_match.group(1).strip()
                if len(body) > 30 and body not in text:
                    text = f"{title} {body}"

            text = re.sub(r"\s+", " ", text).strip()
            if len(text) < 15:
                continue

            posts.append({
                "text": text[:512],  # cap at 512 chars (DistilBERT max)
                "url": url_val,
                "source_feed": url,
            })
        print(f"  [OK]   {url} -> {len(posts)} posts")
        return posts
    except Exception as e:
        print(f"  [ERR]  {url} -> {e}")
        return []


def collect_all() -> list[dict]:
    """Collect from all feeds, deduplicate by URL."""
    all_posts = []
    seen_urls = set()
    seen_texts = set()

    for feed_url in RSS_FEEDS:
        if not feed_url.endswith(".rss") and "rss" not in feed_url:
            continue  # skip non-RSS entries in the list
        posts = fetch_rss(feed_url)
        for post in posts:
            url_key = post["url"]
            text_key = post["text"][:60].lower()
            if url_key and url_key in seen_urls:
                continue
            if text_key in seen_texts:
                continue
            seen_urls.add(url_key)
            seen_texts.add(text_key)
            all_posts.append(post)
        time.sleep(1)  # polite rate limit

    print(f"\nTotal unique posts collected: {len(all_posts)}")
    return all_posts


def label_dataset(posts: list[dict]) -> list[dict]:
    """Apply heuristic labels to all posts."""
    labeled = []
    counts = {"analysis": 0, "hot_take": 0, "reaction": 0}
    for post in posts:
        label, confidence = score_label(post["text"])
        note = f"auto-labeled (confidence={confidence}); NEEDS REVIEW"
        labeled.append({
            "text": post["text"],
            "label": label,
            "notes": note,
            "url": post["url"],
        })
        counts[label] += 1
    print("\nAuto-label distribution:")
    for lbl, cnt in counts.items():
        print(f"  {lbl}: {cnt} ({cnt/len(labeled)*100:.1f}%)")
    return labeled


def save_csv(rows: list[dict], path: str, fieldnames: list[str]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows -> {path}")


def main():
    print("=== TakeMeter Data Collection ===\n")
    print("Fetching r/nba RSS feeds...")
    posts = collect_all()

    # Save raw
    save_csv(posts, "data/raw_posts.csv", ["text", "url", "source_feed"])

    # Label
    print("\nAuto-labeling with heuristics...")
    labeled = label_dataset(posts)

    # Save labeled
    save_csv(labeled, "data/nba_dataset.csv", ["text", "label", "notes", "url"])

    print(f"Done. Next step: open data/nba_dataset.csv and manually review/correct all labels.")
    print("   Each row has a 'notes' field — clear it when you've verified the label.")
    print("   Aim for: analysis ~33%, hot_take ~33%, reaction ~33%")
    print("   Delete the 'url' column before uploading to Colab (keep: text, label, notes).")


if __name__ == "__main__":
    main()
