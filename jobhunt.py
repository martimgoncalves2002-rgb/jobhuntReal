#!/usr/bin/env python3
"""JobHunt (GitHub Actions edition).

Pulls London finance jobs from Adzuna + company ATS feeds, keeps only new
ones, writes index.html (published by GitHub Pages), and emails a digest.

Secrets (Adzuna keys, email login) come from environment variables so they
are NEVER stored in the repo. Everything else lives in config.yaml.

Local testing:
    python jobhunt.py --demo      # sample data, no network, no email
    python jobhunt.py --no-email  # real fetch, skip the email
"""
import os
import sys
import datetime
import yaml

import sources
import filters
import notify


def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"ERROR: {path} not found.")
        sys.exit(1)

    # Overlay secrets from environment (GitHub Actions sets these).
    cfg.setdefault("adzuna", {})
    cfg.setdefault("email", {})
    env = os.environ.get
    if env("ADZUNA_APP_ID"):
        cfg["adzuna"]["app_id"] = env("ADZUNA_APP_ID")
    if env("ADZUNA_APP_KEY"):
        cfg["adzuna"]["app_key"] = env("ADZUNA_APP_KEY")
    if env("EMAIL_USERNAME"):
        cfg["email"]["username"] = env("EMAIL_USERNAME")
    if env("EMAIL_PASSWORD"):
        cfg["email"]["password"] = env("EMAIL_PASSWORD")
    if env("EMAIL_TO"):
        cfg["email"]["to"] = env("EMAIL_TO")
    # Auto-enable email when login is present.
    if cfg["email"].get("username") and cfg["email"].get("password"):
        cfg["email"].setdefault("enabled", True)
    return cfg


DEMO_JOBS = [
    {"id": "demo:1", "title": "Off-Cycle Investment Banking Analyst (Jan 2027)",
     "company": "Meridian Partners", "location": "London, UK", "url": "https://example.com/1",
     "source": "greenhouse:meridian", "posted": "2026-05-28",
     "text": "off-cycle investment banking analyst london 2027 graduate finance m&a"},
    {"id": "demo:2", "title": "Graduate Markets Analyst — Winter 2027 Start",
     "company": "Northgate Capital", "location": "London", "url": "https://example.com/2",
     "source": "lever:northgate", "posted": "",
     "text": "graduate markets analyst trading winter 2027 london early career"},
    {"id": "demo:3", "title": "Software Engineer", "company": "RandomTech",
     "location": "Berlin, Germany", "url": "https://example.com/3", "source": "adzuna",
     "posted": "2026-05-20", "text": "software engineer python berlin"},
    {"id": "demo:4", "title": "Private Equity Analyst Internship",
     "company": "Harbour Equity", "location": "London, United Kingdom", "url": "https://example.com/4",
     "source": "ashby:harbour", "posted": "2026-05-29",
     "text": "private equity analyst internship london finance investment"},
    {"id": "demo:5", "title": "Risk Analyst (Graduate Programme)",
     "company": "Adzuna Listing Co", "location": "London", "url": "https://example.com/5",
     "source": "adzuna", "posted": "2026-05-27",
     "text": "risk analyst graduate programme london banking finance"},
]


def run(demo=False, do_email=True):
    if demo:
        print("DEMO MODE — sample data, no network calls.\n")
        config = {
            "filter": {
                "location_keywords": ["london", "united kingdom", "uk"],
                "must_have": ["finance", "analyst", "investment", "trading",
                              "banking", "private equity", "risk", "graduate", "intern"],
                "boost": ["off-cycle", "2027", "winter", "graduate", "intern", "early career"],
                "min_score": 1,
            },
            "email": {"enabled": False},
            "priority": {
                "enabled": True,
                "keywords": ["off-cycle", "2027", "winter"],
            },
            "dashboard": {"path": "index.html"},
        }
        raw = DEMO_JOBS
        seen_path = "seen_demo.json"
    else:
        config = load_config()
        seen_path = "seen.json"
        print("Fetching sources...")
        raw = sources.fetch_all(config)

    print(f"\nFetched {len(raw)} raw listings.")
    kept = filters.filter_jobs(raw, config.get("filter") or {})
    print(f"{len(kept)} relevant after filtering.")

    seen = filters.load_seen(seen_path)
    new = filters.split_new(seen, kept, seen_path)
    new_ids = {j["id"] for j in new}
    print(f"{len(new)} are NEW since last run.")

    dash = (config.get("dashboard") or {}).get("path", "index.html")
    notify.build_dashboard(kept, new_ids, dash)
    # .nojekyll lets GitHub Pages serve index.html as-is
    open(".nojekyll", "w").close()
    print(f"Dashboard written -> {dash}")

    # Build the priority subset: new roles matching grad/off-cycle/2027 signals.
    pcfg = config.get("priority") or {}
    pnew = []
    if pcfg.get("enabled"):
        kws = [k.lower() for k in pcfg.get("keywords", [])]
        pnew = [j for j in new
                if any(k in j.get("text", "").lower() for k in kws)]
        print(f"{len(pnew)} of those match the priority focus.")

    if do_email:
        ecfg = config.get("email") or {}
        notify.send_email(ecfg, new, dash)          # broad digest (all new)
        if pcfg.get("enabled"):                      # focused digest (subset)
            today = datetime.date.today().isoformat()
            notify.send_email(
                ecfg, pnew, dash,
                subject=f"⭐ {len(pnew)} priority roles (grad / off-cycle 2027) — {today}",
                to=(pcfg.get("to") or None),
                heading="Priority — graduate / off-cycle / winter-2027 starts",
            )

    return kept, new


if __name__ == "__main__":
    run(demo="--demo" in sys.argv, do_email="--no-email" not in sys.argv)
