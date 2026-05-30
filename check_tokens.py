#!/usr/bin/env python3
"""check_tokens.py — find which company ATS tokens actually work.

Run this once (locally or as a GitHub Action). For every candidate token it
tries the Greenhouse, Lever, and Ashby feeds and reports which return jobs.
Copy the winners into config.yaml under `ats:`.

    python check_tokens.py

Edit the CANDIDATES lists below to test your own guesses. A token is just the
company slug from its careers URL:
    boards.greenhouse.io/SLUG   jobs.lever.co/SLUG   jobs.ashbyhq.com/SLUG
"""
import requests

H = {"User-Agent": "JobHunt-TokenCheck/1.0"}
T = 20

# ---- Candidate tokens to test (educated guesses; edit freely) -------------
# Leaning toward firms most likely to use these ATS: funds, fintech, prop,
# boutiques. Bulge brackets / big banks are mostly on Workday (no feed).
CANDIDATES = {
    "greenhouse": [
        "mangroup", "marshallwace", "brevanhoward", "winton", "capula",
        "lansdownepartners", "systematica", "aspectcapital", "rokoscapital",
        "eislercapital", "cheynecapital", "triumcapital", "balyasny", "aqrcapital",
        "citadel", "citadelsecurities", "point72", "milleniummanagement",
        "janestreet", "optiver", "imc", "drw", "xtxmarkets",
        "revolut", "wise", "monzo", "starlingbank", "checkout", "gocardless",
        "oaknorth", "clearbank", "thoughtmachine", "ebury",
        "blackstone", "kkr", "carlyle", "eqtpartners", "cvc", "permira",
        "apax", "cinven", "bridgepoint", "icg", "3i", "tdrcapital",
        "hgcapital", "vitruvianpartners", "generalatlantic", "tpg",
        "warburgpincus", "advent", "baincapital", "harbourvest", "collercapital",
        "schroders", "manmgroup", "baillie-gifford", "bailliegifford",
        "janushenderson", "jupiteram", "ninetyone", "mandg",
        "lseg", "tradeweb", "msci", "spglobal", "bloomberg",
        "stjamesplace", "quilter", "evelynpartners", "rathbones",
        "ftic", "ftconsulting", "alixpartners", "teneo", "kroll", "interpath",
        "lazard", "rothschildandco", "evercore", "houlihanlokey", "pjtpartners",
        "moelis", "perellaweinberg", "jefferies", "stifel", "peelhunt",
    ],
    "lever": [
        "fnz", "ebury", "gocardless", "checkout", "oaknorth", "wintoncapital",
        "marshallwace", "eisler", "cheyne", "quanthouse", "xtx",
    ],
    "ashby": [
        "qube-rt", "quant", "ramp", "checkout", "thoughtmachine", "oaknorth",
        "clearbank", "gocardless", "wise", "monzo", "starling",
    ],
}


def try_greenhouse(t):
    u = f"https://boards-api.greenhouse.io/v1/boards/{t}/jobs"
    try:
        r = requests.get(u, headers=H, timeout=T)
        if r.status_code == 200:
            return len(r.json().get("jobs", []))
    except Exception:
        pass
    return None


def try_lever(t):
    u = f"https://api.lever.co/v0/postings/{t}?mode=json&limit=5"
    try:
        r = requests.get(u, headers=H, timeout=T)
        if r.status_code == 200 and isinstance(r.json(), list):
            return len(r.json())
    except Exception:
        pass
    return None


def try_ashby(t):
    u = f"https://api.ashbyhq.com/posting-api/job-board/{t}"
    try:
        r = requests.get(u, headers=H, timeout=T)
        if r.status_code == 200:
            return len(r.json().get("jobs", []))
    except Exception:
        pass
    return None


CHECKERS = {"greenhouse": try_greenhouse, "lever": try_lever, "ashby": try_ashby}


def main():
    winners = {"greenhouse": [], "lever": [], "ashby": []}
    for platform, tokens in CANDIDATES.items():
        check = CHECKERS[platform]
        print(f"\n===== {platform.upper()} =====")
        for t in tokens:
            n = check(t)
            if n is not None:
                flag = "  <-- LIVE" if n > 0 else "  (live but 0 jobs now)"
                print(f"  ✅ {t:24} {n} jobs{flag}")
                if n > 0:
                    winners[platform].append(t)
            else:
                print(f"  ✗  {t:24} no feed")

    print("\n\n================ COPY THESE INTO config.yaml ================")
    print("ats:")
    for platform in ("greenhouse", "lever", "ashby"):
        print(f"  {platform}:")
        for t in winners[platform]:
            print(f'    - "{t}"')
    print("============================================================")
    total = sum(len(v) for v in winners.values())
    print(f"\n{total} working tokens found.")


if __name__ == "__main__":
    main()
