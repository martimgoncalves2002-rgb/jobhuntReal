"""Fetch job listings from Adzuna and public ATS feeds (Greenhouse, Lever, Ashby).

Every fetcher returns a list of normalized dicts with this shape:
    {
      "id":       "source:nativeid",   # stable unique key for dedup
      "title":    str,
      "company":  str,
      "location": str,
      "url":      str,                 # apply / listing link
      "source":   str,                 # "adzuna" | "greenhouse:wise" | ...
      "posted":   str,                 # ISO date if known, else ""
      "text":     str,                 # title + description, for keyword matching
    }
Network errors never crash the run — a failed source just returns [].
"""
import html
import re
import hashlib
import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "JobHunt/1.0 (personal job tracker)"}


def _strip_html(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def _hash(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- Adzuna
def fetch_adzuna(cfg):
    app_id = (cfg or {}).get("app_id") or ""
    app_key = (cfg or {}).get("app_key") or ""
    if not app_id or not app_key:
        return []
    country = cfg.get("country", "gb")
    where = cfg.get("where", "London")
    rpp = int(cfg.get("results_per_page", 50))
    pages = int(cfg.get("pages", 1))
    max_days = int(cfg.get("max_days_old", 7))
    out = []
    for query in cfg.get("queries", []):
        for page in range(1, pages + 1):
            url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": query,
                "where": where,
                "results_per_page": rpp,
                "max_days_old": max_days,
                "content-type": "application/json",
            }
            try:
                r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"  [adzuna] '{query}' p{page} failed: {e}")
                break
            results = data.get("results", [])
            if not results:
                break
            for j in results:
                jid = str(j.get("id", "")) or _hash(j.get("redirect_url", ""))
                title = j.get("title", "") or ""
                desc = j.get("description", "") or ""
                out.append({
                    "id": f"adzuna:{jid}",
                    "title": _strip_html(title),
                    "company": (j.get("company") or {}).get("display_name", "Unknown"),
                    "location": (j.get("location") or {}).get("display_name", ""),
                    "url": j.get("redirect_url", ""),
                    "source": "adzuna",
                    "posted": (j.get("created", "") or "")[:10],
                    "text": _strip_html(title + " " + desc),
                })
            if len(results) < rpp:
                break
    return out


# ----------------------------------------------------------- Greenhouse
def fetch_greenhouse(token):
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
    except Exception as e:
        print(f"  [greenhouse:{token}] failed: {e}")
        return []
    out = []
    for j in jobs:
        out.append({
            "id": f"greenhouse:{token}:{j.get('id')}",
            "title": _strip_html(j.get("title", "")),
            "company": j.get("company_name") or token,
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "source": f"greenhouse:{token}",
            "posted": (j.get("updated_at", "") or "")[:10],
            "text": _strip_html(j.get("title", "") + " " + (j.get("content", "") or "")),
        })
    return out


# ----------------------------------------------------------------- Lever
def fetch_lever(site):
    url = f"https://api.lever.co/v0/postings/{site}?mode=json&limit=200"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        jobs = r.json()
    except Exception as e:
        print(f"  [lever:{site}] failed: {e}")
        return []
    out = []
    for j in jobs if isinstance(jobs, list) else []:
        cats = j.get("categories") or {}
        out.append({
            "id": f"lever:{site}:{j.get('id')}",
            "title": _strip_html(j.get("text", "")),
            "company": site,
            "location": cats.get("location", ""),
            "url": j.get("hostedUrl") or j.get("applyUrl", ""),
            "source": f"lever:{site}",
            "posted": "",
            "text": _strip_html(j.get("text", "") + " " + (j.get("descriptionPlain", "") or "")),
        })
    return out


# ----------------------------------------------------------------- Ashby
def fetch_ashby(board):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
    except Exception as e:
        print(f"  [ashby:{board}] failed: {e}")
        return []
    out = []
    for j in jobs:
        out.append({
            "id": f"ashby:{board}:{j.get('id')}",
            "title": _strip_html(j.get("title", "")),
            "company": board,
            "location": j.get("location", "") or "",
            "url": j.get("jobUrl") or j.get("applyUrl", ""),
            "source": f"ashby:{board}",
            "posted": (j.get("publishedAt", "") or "")[:10],
            "text": _strip_html(j.get("title", "") + " " + (j.get("descriptionPlain", "") or "")),
        })
    return out


def fetch_all(config):
    """Run every configured source and return a flat list of jobs."""
    jobs = []
    adz = fetch_adzuna(config.get("adzuna") or {})
    print(f"  adzuna: {len(adz)}")
    jobs += adz
    ats = config.get("ats") or {}
    for token in ats.get("greenhouse", []) or []:
        g = fetch_greenhouse(token)
        print(f"  greenhouse:{token}: {len(g)}")
        jobs += g
    for site in ats.get("lever", []) or []:
        l = fetch_lever(site)
        print(f"  lever:{site}: {len(l)}")
        jobs += l
    for board in ats.get("ashby", []) or []:
        a = fetch_ashby(board)
        print(f"  ashby:{board}: {len(a)}")
        jobs += a
    return jobs
