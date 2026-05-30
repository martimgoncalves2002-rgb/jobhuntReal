"""Relevance scoring + a JSON 'seen' store so we only alert on NEW jobs.
JSON (not SQLite) so it commits back to GitHub cleanly as readable text."""
import json
import datetime


# ----------------------------------------------------------- filtering
def score_job(job, fcfg):
    """Return (score, tags). score<min_score or wrong location => dropped."""
    text = (job.get("text", "") + " " + job.get("location", "")).lower()
    loc = job.get("location", "").lower()

    loc_kw = [k.lower() for k in fcfg.get("location_keywords", [])]
    if loc_kw and not any(k in loc or k in text for k in loc_kw):
        return -1, []

    score = 0
    for kw in fcfg.get("must_have", []):
        if kw.lower() in text:
            score += 1
    tags = []
    for kw in fcfg.get("boost", []):
        if kw.lower() in text:
            score += 2
            tag = kw.strip().title()
            if tag not in tags:
                tags.append(tag)
    return score, tags


def filter_jobs(jobs, fcfg):
    min_score = int(fcfg.get("min_score", 1))
    kept = []
    for j in jobs:
        score, tags = score_job(j, fcfg)
        if score >= min_score:
            j["score"] = score
            j["tags"] = tags
            kept.append(j)
    kept.sort(key=lambda x: x["score"], reverse=True)
    return kept


# -------------------------------------------------------------- storage
def load_seen(path="seen.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def split_new(seen, jobs, path="seen.json"):
    """Add unseen job ids to `seen`, save it, return the list of new jobs."""
    today = datetime.date.today().isoformat()
    new = []
    for j in jobs:
        if j["id"] in seen:
            continue
        seen[j["id"]] = today
        new.append(j)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=0, sort_keys=True)
    return new
