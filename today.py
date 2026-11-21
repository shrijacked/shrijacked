"""Nightly stats refresh for the neofetch card (same idea as Andrew6rant/today.py, simplified).
Queries GitHub GraphQL, writes stats.json, then re-renders dark_mode.svg / light_mode.svg.
Env: ACCESS_TOKEN (fine-grained PAT, read-only: metadata + contents; or the workflow GITHUB_TOKEN), USER_NAME."""
import datetime as dt, json, os, subprocess, sys, urllib.request

TOKEN, USER = os.environ["ACCESS_TOKEN"], os.environ.get("USER_NAME", "shrijacked")

def gql(query, variables):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]

Q = """query($login:String!, $cursor:String){ user(login:$login){
  createdAt
  followers{ totalCount }
  repositories(first:100, after:$cursor, ownerAffiliations:OWNER){ totalCount
    pageInfo{ hasNextPage endCursor } nodes{ stargazerCount isFork } }
  contributionsCollection{ totalCommitContributions restrictedContributionsCount
    contributionCalendar{ totalContributions weeks{ contributionDays{ contributionCount } } } } } }"""

def plural(n, w): return f"{n} {w}{'' if n == 1 else 's'}"

def uptime(since):
    now = dt.date.today()
    y, m, d = now.year - since.year, now.month - since.month, now.day - since.day
    if d < 0:
        m -= 1
        d += (now.replace(day=1) - dt.timedelta(days=1)).day
    if m < 0:
        y, m = y - 1, m + 12
    return f"{plural(y, 'year')}, {plural(m, 'month')}, {plural(d, 'day')}"

def main():
    cursor, stars, data = None, 0, None
    while True:
        u = gql(Q, {"login": USER, "cursor": cursor})["user"]
        data = data or u
        stars += sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
        pi = u["repositories"]["pageInfo"]
        if not pi["hasNextPage"]: break
        cursor = pi["endCursor"]
    cc = data["contributionsCollection"]
    days = [d["contributionCount"] for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    best = run = 0
    for c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    stats = {
        "uptime": uptime(dt.date.fromisoformat(data["createdAt"][:10])),
        "repos": f"{data['repositories']['totalCount']:,}",
        "stars": f"{stars:,}",
        "commits": f"{cc['totalCommitContributions']:,}",
        "followers": f"{data['followers']['totalCount']:,}",
        "contributions": f"{cc['contributionCalendar']['totalContributions']:,}",
        "streak": plural(best, "day"),
        "_note": f"generated {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC by today.py",
    }
    here = os.path.dirname(os.path.abspath(__file__))
    json.dump(stats, open(os.path.join(here, "stats.json"), "w"), indent=1)
    subprocess.run([sys.executable, os.path.join(here, "build_svg.py")], check=True)
    print(json.dumps(stats, indent=1))

if __name__ == "__main__":
    main()
