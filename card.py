#!/usr/bin/env python3
"""Build the profile card, light and dark, from live GitHub numbers.

The card is a neofetch parody: ASCII art on the left, key/dots/value rows on the
right. The numbers at the bottom come from the GitHub GraphQL API and are
rewritten by .github/workflows/card.yml, so they are current without anyone
remembering to update them.

Both themes are rendered from ONE layout, defined once in `rows()`. The obvious
alternative is to keep two hand-written SVGs and substitute values into them by
element id, which is how this kind of card is usually done - and it means every
layout change has to be made twice, correctly, or the two themes quietly drift
apart. Here a theme is a palette and nothing else.

Alignment does not depend on the font metrics being right. Every dot leader is
computed in characters and the face is monospace, so the columns line up
whatever the renderer substitutes; the pixel width only decides how much empty
canvas sits to the right.

Usage:
    GITHUB_TOKEN=... python3 card.py            # fetch, then write both SVGs
    python3 card.py --offline                   # re-render from cache.json only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache.json"
API = "https://api.github.com/graphql"

LOGIN = "SuneethJerri"

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

FONT_SIZE = 15
LINE_H = 19
CHAR_W = 9.45         # only affects canvas size and the panel's left edge
                      # Deliberately above the 9.03 that DejaVu Sans Mono
                      # actually advances at 15px. The dot leaders are
                      # computed in characters, so a face wider than the
                      # estimate does not misalign anything - it just runs
                      # off the right edge of the canvas. The slack is the
                      # cheapest way to make that impossible.
MARGIN = 18
PANEL_COLS = 66       # the dot leaders are computed against this

# A quadcopter, because the drone is the one thing here that had to work
# outdoors. Kept to 40 columns so the panel starts at a predictable x.
ART = r"""
   .-''-.                            .-''-.
  /      \__                      __/      \
 |   ()   | \__                __/ |   ()   |
  \      /    \__            __/    \      /
   '-..-'       \__        __/       '-..-'
                   \______/
                   |      |
                   | [oo] |
                   |______|
                 __/      \__
   .-''-.     __/            \__     .-''-.
  /      \ __/                  \__ /      \
 |   ()   |                        |   ()   |
  \      /                          \      /
   '-..-'                            '-..-'
"""

THEMES = {
    "dark": {
        "bg": "#0d1117", "edge": "#30363d", "text": "#c9d1d9", "art": "#7d8590",
        "key": "#ffa657", "value": "#a5d6ff", "dots": "#484f58",
        "rule": "#30363d", "add": "#3fb950", "sub": "#f85149",
    },
    "light": {
        "bg": "#ffffff", "edge": "#d0d7de", "text": "#1f2328", "art": "#6e7781",
        "key": "#953800", "value": "#0550ae", "dots": "#afb8c1",
        "rule": "#d0d7de", "add": "#1a7f37", "sub": "#cf222e",
    },
}


def rows(s: dict) -> list:
    """The card's content. Each entry is one of:

    ("head", left)      a section rule
    ("kv", key, value)  a key/dots/value line
    ("raw", segments)   pre-coloured segments, for the mixed stats lines
    None                a blank line
    """
    return [
        ("title", f"{LOGIN.lower()}@github"),
        ("kv", "Role", "M.Tech, Robotics and Machine Intelligence"),
        ("kv", "Host", "IIIT Allahabad"),
        ("kv", "Prev", "B.Tech CSE, Keshav Memorial Inst. of Technology"),
        ("kv", "Uptime", s["uptime"]),
        None,
        ("head", "Research"),
        ("kv", "Thesis", "Encrypted VPN traffic under concept drift"),
        ("kv", "Thesis.Method", "Active learning + RL drift meta-controller"),
        ("kv", "Vision", "Attention grounding for VLM hallucination"),
        ("kv", "Vision.Result", "-50% hallucinated objects on CHAIR"),
        ("kv", "Robotics", "Autonomous UAV target detection and tracking"),
        None,
        ("head", "Stack"),
        ("kv", "Languages.Programming", "Python, C/C++, Java, JavaScript, SQL"),
        ("kv", "Languages.ML", "PyTorch, Hugging Face, scikit-learn, OpenCV"),
        ("kv", "Languages.Systems", "Postgres, FastAPI, Django, React"),
        ("kv", "Tools", "Git, Linux, Docker, Wireshark"),
        None,
        ("head", "Contact"),
        ("kv", "Email", "suneeth47@gmail.com"),
        ("kv", "LinkedIn", "suneeth-jerri"),
        None,
        ("head", "GitHub"),
        ("stats", s),
    ]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def leader(key: str, value: str, width: int = PANEL_COLS) -> int:
    """Dots between `key:` and `value`, at least one on each side."""
    used = len(key) + 1 + len(value) + 2
    return max(1, width - used)


def line_kv(x: float, y: int, key: str, value: str) -> str:
    dots = "." * leader(key, value)
    # A dotted key like Languages.ML gets both halves in the key colour, with
    # the separator left plain, which is what makes the grouping readable.
    parts = key.split(".")
    head = '<tspan class="k">.</tspan>'.join(
        f'<tspan class="k">{escape(p)}</tspan>' for p in parts
    )
    return (
        f'<tspan x="{x}" y="{y}"><tspan class="d">. </tspan>{head}'
        f'<tspan class="d">: {dots} </tspan>'
        f'<tspan class="v">{escape(value)}</tspan></tspan>'
    )


def line_head(x: float, y: int, label: str) -> str:
    rule = "-" * max(1, PANEL_COLS - len(label) - 4)
    return (
        f'<tspan x="{x}" y="{y}"><tspan class="t">- {escape(label)} </tspan>'
        f'<tspan class="r">{rule}</tspan></tspan>'
    )


def line_title(x: float, y: int, label: str) -> str:
    rule = "-" * max(1, PANEL_COLS - len(label) - 1)
    return (
        f'<tspan x="{x}" y="{y}"><tspan class="t">{escape(label)} </tspan>'
        f'<tspan class="r">{rule}</tspan></tspan>'
    )


def line_stats(x: float, y0: int, s: dict) -> list[str]:
    """Three lines whose values sit inline rather than at a leader column."""
    def kv(key: str, value: str, width: int) -> str:
        dots = "." * max(1, width - len(key) - len(value) - 3)
        return (
            f'<tspan class="k">{escape(key)}</tspan>'
            f'<tspan class="d">: {dots} </tspan>'
            f'<tspan class="v">{escape(value)}</tspan>'
        )

    out = [
        f'<tspan x="{x}" y="{y0}"><tspan class="d">. </tspan>'
        + kv("Repos", s["repos"], 28)
        + '<tspan class="d">  |  </tspan>'
        + kv("Stars", s["stars"], 30)
        + "</tspan>",
        f'<tspan x="{x}" y="{y0 + LINE_H}"><tspan class="d">. </tspan>'
        + kv("Commits", s["commits"], 28)
        + '<tspan class="d">  |  </tspan>'
        + kv("Followers", s["followers"], 30)
        + "</tspan>",
    ]
    loc, add, sub = s["loc"], s["added"], s["deleted"]
    tail = f"( {add}++, {sub}-- )"
    dots = "." * max(1, PANEL_COLS - len("Lines of code") - len(loc) - len(tail) - 6)
    out.append(
        f'<tspan x="{x}" y="{y0 + 2 * LINE_H}"><tspan class="d">. </tspan>'
        f'<tspan class="k">Lines of code</tspan><tspan class="d">: {dots} </tspan>'
        f'<tspan class="v">{escape(loc)}</tspan><tspan class="d"> ( </tspan>'
        f'<tspan class="a">{escape(add)}++</tspan><tspan class="d">, </tspan>'
        f'<tspan class="s">{escape(sub)}--</tspan><tspan class="d"> )</tspan></tspan>'
    )
    return out


def render(stats: dict, theme: str) -> str:
    c = THEMES[theme]
    art = ART.strip("\n").split("\n")
    art_cols = max(len(line) for line in art)
    panel_x = MARGIN + art_cols * CHAR_W + 2 * CHAR_W

    body: list[str] = []
    y = MARGIN + FONT_SIZE
    for row in rows(stats):
        if row is None:
            y += LINE_H
            continue
        kind = row[0]
        if kind == "title":
            body.append(line_title(panel_x, y, row[1]))
        elif kind == "head":
            body.append(line_head(panel_x, y, row[1]))
        elif kind == "kv":
            body.append(line_kv(panel_x, y, row[1], row[2]))
        elif kind == "stats":
            body.extend(line_stats(panel_x, y, row[1]))
            y += 2 * LINE_H
        y += LINE_H

    # The panel is a dozen lines taller than the art, so a top-aligned drone
    # leaves a hole in the bottom-left corner of the card. Centred against the
    # panel it reads as one composition instead of two columns that happen to
    # share a background.
    panel_h = y - (MARGIN + FONT_SIZE)
    art_h = len(art) * LINE_H
    art_y = MARGIN + FONT_SIZE + max(0, round((panel_h - art_h) / 2))
    art_lines = "".join(
        f'<tspan x="{MARGIN}" y="{art_y + i * LINE_H}">{escape(line)}</tspan>'
        for i, line in enumerate(art)
    )

    width = round(panel_x + PANEL_COLS * CHAR_W + MARGIN)
    height = max(y, art_y + art_h) + MARGIN - LINE_H + 6

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}px" height="{height}px"
     font-family="Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace"
     font-size="{FONT_SIZE}px">
<style>
text, tspan {{ white-space: pre; }}
.k {{ fill: {c['key']}; }}
.v {{ fill: {c['value']}; }}
.d {{ fill: {c['dots']}; }}
.r {{ fill: {c['rule']}; }}
.t {{ fill: {c['text']}; }}
.a {{ fill: {c['add']}; }}
.s {{ fill: {c['sub']}; }}
</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"
      fill="{c['bg']}" stroke="{c['edge']}"/>
<text xml:space="preserve" fill="{c['art']}">{art_lines}</text>
<text xml:space="preserve" fill="{c['text']}">{"".join(body)}</text>
</svg>
"""


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

class ApiError(RuntimeError):
    pass


def graphql(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    request = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-card",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        raise ApiError(f"HTTP {exc.code} from the GraphQL API") from exc
    if "errors" in payload:
        raise ApiError("; ".join(e.get("message", "?") for e in payload["errors"]))
    return payload["data"]


PROFILE_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    id
    createdAt
    followers { totalCount }
    repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST]) { totalCount }
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER,
                 orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        nameWithOwner
        isFork
        stargazerCount
        defaultBranchRef { target { ... on Commit { oid } } }
      }
    }
  }
}
"""

HISTORY_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $after: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $after, author: {id: $id}) {
            totalCount
            pageInfo { hasNextPage endCursor }
            nodes { additions deletions }
          }
        }
      }
    }
  }
}
"""


def uptime_since(created: str) -> str:
    """Whole years, months and days on GitHub, as neofetch would print it."""
    start = datetime.fromisoformat(created.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    years = now.year - start.year
    months = now.month - start.month
    days = now.day - start.day
    if days < 0:
        months -= 1
        previous = (now.month - 1) or 12
        year = now.year if now.month > 1 else now.year - 1
        days += (datetime(year, previous % 12 + 1, 1, tzinfo=timezone.utc)
                 - datetime(year, previous, 1, tzinfo=timezone.utc)).days
    if months < 0:
        years -= 1
        months += 12
    parts = []
    if years:
        parts.append(f"{years} year{'s' * (years != 1)}")
    parts.append(f"{months} month{'s' * (months != 1)}")
    parts.append(f"{days} day{'s' * (days != 1)}")
    return ", ".join(parts)


def repo_loc(owner: str, name: str, user_id: str, token: str) -> tuple[int, int]:
    """Lines this user added and deleted on a repository's default branch."""
    added = deleted = 0
    cursor = None
    while True:
        data = graphql(
            HISTORY_QUERY,
            {"owner": owner, "name": name, "id": user_id, "after": cursor},
            token,
        )
        ref = (data.get("repository") or {}).get("defaultBranchRef")
        if not ref:
            return added, deleted
        history = ref["target"]["history"]
        for node in history["nodes"]:
            added += node["additions"]
            deleted += node["deletions"]
        if not history["pageInfo"]["hasNextPage"]:
            return added, deleted
        cursor = history["pageInfo"]["endCursor"]


def collect(token: str) -> dict:
    """Fetch everything the card shows, reusing cached line counts.

    Line counting is the expensive call by a wide margin: it walks every commit
    on every default branch. The cache is keyed on the branch head, so a repo
    that has not moved since the last run costs nothing, and one that has is
    recounted in full rather than diffed - at this number of repositories that
    is simpler and no slower.
    """
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    repos_cache = cache.get("repos", {})

    nodes, cursor = [], None
    while True:
        data = graphql(PROFILE_QUERY, {"login": LOGIN, "after": cursor}, token)
        user = data["user"]
        page = user["repositories"]
        nodes.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    owned = [n for n in nodes if not n["isFork"]]
    added = deleted = 0
    fresh: dict[str, dict] = {}
    for node in owned:
        full = node["nameWithOwner"]
        target = (node.get("defaultBranchRef") or {}).get("target") or {}
        head = target.get("oid")
        if head is None:
            continue
        previous = repos_cache.get(full)
        if previous and previous.get("head") == head:
            entry = previous
        else:
            owner, name = full.split("/", 1)
            a, d = repo_loc(owner, name, user["id"], token)
            entry = {"head": head, "added": a, "deleted": d}
        fresh[full] = entry
        added += entry["added"]
        deleted += entry["deleted"]

    contributions = user["contributionsCollection"]
    commits = (contributions["totalCommitContributions"]
               + contributions["restrictedContributionsCount"])

    stats = {
        "uptime": uptime_since(user["createdAt"]),
        "repos": f"{len(owned):,}",
        "contributed": f"{user['repositoriesContributedTo']['totalCount']:,}",
        "stars": f"{sum(n['stargazerCount'] for n in owned):,}",
        "commits": f"{commits:,}",
        "followers": f"{user['followers']['totalCount']:,}",
        "loc": f"{added - deleted:,}",
        "added": f"{added:,}",
        "deleted": f"{deleted:,}",
    }
    CACHE.write_text(json.dumps({"stats": stats, "repos": fresh}, indent=2) + "\n")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline", action="store_true",
        help="Re-render from cache.json without calling the API.",
    )
    args = parser.parse_args()

    if args.offline:
        if not CACHE.exists():
            print("no cache.json to render from", file=sys.stderr)
            return 1
        stats = json.loads(CACHE.read_text())["stats"]
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN")
        if not token:
            print("set GITHUB_TOKEN (or pass --offline)", file=sys.stderr)
            return 1
        try:
            stats = collect(token)
        except ApiError as exc:
            # A failed run must not blank the card. Fall back to the last known
            # numbers and say so, rather than committing an SVG full of zeroes.
            if not CACHE.exists():
                print(f"first run failed and there is no cache: {exc}", file=sys.stderr)
                return 1
            print(f"::warning::{exc}; rendering from cache", file=sys.stderr)
            stats = json.loads(CACHE.read_text())["stats"]

    for theme in THEMES:
        (HERE / f"card-{theme}.svg").write_text(render(stats, theme))
    print(f"wrote card-light.svg and card-dark.svg  ({stats['loc']} lines of code)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
