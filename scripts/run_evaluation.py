"""
NBA Data Agent Evaluation Runner
Sends all test-plan questions to the BigQuery Conversational Analytics agent
and writes results to analysis/evaluation_log.md.
"""

import argparse
import google.auth
import google.auth.transport.requests
import requests
import json
import time
import os
import sys
from datetime import date

import agent_config

# Force unbuffered stdout so tee captures output live
sys.stdout.reconfigure(line_buffering=True)

# Set by main() from --target (dev default; --target prod = live agent)
CFG = None

DELAY_BETWEEN_QUESTIONS = 2  # seconds

# Resolved once per run by resolve_output_path(); every run gets its own
# dated, indexed file under analysis/eval_runs/ and never overwrites a
# previous log. The legacy evaluation_log*.md files are historical
# artifacts — no run writes to them anymore.
OUTPUT_PATH = None

def resolve_output_path(suite):
    run_dir = os.path.join(os.path.dirname(__file__), "../analysis/eval_runs")
    os.makedirs(run_dir, exist_ok=True)
    today = date.today().isoformat()
    for n in range(1, 100):
        candidate = os.path.join(run_dir, f"{today}_{CFG['target']}_{suite}_run{n:02d}.md")
        if not os.path.exists(candidate):
            return candidate
    raise SystemExit(f"100 runs for {CFG['target']} on {today}?! Clean up {run_dir}.")

def output_path():
    return OUTPUT_PATH

# ── Test questions ─────────────────────────────────────────────────────────────

# Original June 2026 suite — FROZEN for drift comparisons (--suite legacy).
# Do not edit: identical inputs are what make June-vs-now deltas attributable
# to the service rather than to us.
LEGACY_PART1 = [
    # (q_num, question, expected_answer_summary)
    (1,  "What did LeBron James average in points, rebounds, and assists per game in the 2012-13 season?",
         "26.8 PPG, 8.0 RPG, 7.3 APG"),
    (2,  "Which players averaged 35 or more points per game in a season since 1984, and who led?",
         "4 seasons: Jordan 37.1 (1986-87), Harden 36.1 (2018-19), Kobe 35.4 (2005-06), Jordan 35.0 (1987-88)"),
    (3,  "What was Stephen Curry's 3-point field goal percentage in the 2015-16 season?",
         "45.4%"),
    (4,  "Which player had the highest single-season VORP in the dataset?",
         "Michael Jordan 1987-88 (VORP = 12.5, CHI); LeBron 2008-09 is 2nd (11.8)"),
    (5,  "How many seasons did Michael Jordan appear in the dataset, and what was his career average PPG across those seasons?",
         "15 seasons, 29.5 career PPG"),
    (6,  "Which team had the best Net Rating in the 2015-16 season?",
         "San Antonio Spurs (11.3 NRtg, 67-15); GSW was 2nd (10.7)"),
    (7,  "Which team had the highest SRS in any season in the dataset?",
         "OKC 2024-25 (SRS = 12.7); CHI 1995-96 is 2nd (11.8)"),
    (8,  "How has league average pace changed from the 1994-95 season to the 2018-19 season?",
         "~92.9 in 1995, trough ~90.9 in 2005, back to 100.0 in 2019"),
    (9,  "What were the top 3 teams by offensive rating in the 2015-16 season?",
         "GSW (114.5), OKC (113.1), CLE (110.9)"),
    (10, "How many wins did the Golden State Warriors have in the 2015-16 regular season?",
         "73 wins (NBA record)"),
    (11, "What was the Chicago Bulls' win-loss record in the 1995-96 season?",
         "72-10 (data IS available; season = 1996)"),
    (12, "How many road wins did the Miami Heat record in the 2012-13 regular season?",
         "29 road wins"),
    (13, "What was the Golden State Warriors' home record in the 2015-16 season?",
         "39-2 at home"),
    (14, "How many games did the 2016 NBA Finals last?",
         "7 games (Cleveland defeated Golden State)"),
    (15, "How many consecutive NBA Finals appearances did the Golden State Warriors make starting in 2015?",
         "5 consecutive (2015-2019); also appeared in 2022"),
    (16, "Which team did the Detroit Pistons defeat in the 2004 NBA Finals, and what was the series length?",
         "Los Angeles Lakers, 4-1 (5 games)"),
    (17, "How many total playoff series have been played in the dataset?",
         "~630 series"),
    (18, "Which team acquired James Harden in an in-season trade, and when?",
         "3 trades: BRK from HOU (Jan 2021), PHI from BRK (Feb 2022), LAC from PHI (Nov 2023)"),
    (19, "Which team did Pau Gasol join after his February 2008 trade, and which team traded him?",
         "LAL acquired from MEM on 2008-02-01"),
    (20, "Which team showed the largest improvement in Net Rating in the season following a major in-season trade?",
         "DET 2024-25: NRtg went from -9.1 to +8.2 (+17.3 delta)"),
    (21, "What was the Net Rating of the team LeBron James played for in his highest-VORP season?",
         "Requires join: LeBron highest VORP = 11.8 (CLE, 2008-09)"),
    (22, "Which teams won a playoff series in the same season a star player (top-10 VORP) was traded to them mid-season?",
         "Multi-hop; verify against data"),
    (23, "In the 2016 NBA Finals, what were the regular-season Net Ratings of both teams?",
         "CLE and GSW NRtg in 2015-16 (season=2016)"),
]

LEGACY_PART2 = [
    # (q_num, question, expected_behavior)
    (1, "What was the Chicago Bulls' game-by-game record in the 1994-95 season?",
        "Must state game logs only go back to 1995-96 (season=1996); cannot answer for 1994-95"),
    (2, "Who did the Lakers trade for before 1997?",
        "Must state trade data starts in 1997; cannot answer for earlier trades"),
    (3, "What will the Lakers' Net Rating be next season?",
        "Must decline — data does not include future seasons"),
    (4, "Who is the greatest NBA player of all time?",
        "Must caveat as subjective; may offer data-supported framing but no definitive answer"),
    (5, "How many points did Wilt Chamberlain average in 1961-62?",
        "Must state player data starts in 1984; cannot answer for 1961-62"),
    (6, "What were Chet Holmgren's stats last week?",
        "Must state data is not real-time; most recent data is end of 2025-26 season"),
]

# 2026-07-03 revised suite (--suite v2, default). Tier tags and full rubrics
# live in analysis/agent_test_plan.md; the expected strings here are grader
# reminders, not the authoritative answer key.
SUITE_PART1 = [
    (1,  "What did LeBron James average in points, rebounds, and assists per game in the 2012-13 season?",
         "26.8 PPG, 8.0 RPG, 7.3 APG"),
    (2,  "Which players averaged 35 or more points per game in a season since 1984, and who led?",
         "4 seasons / 3 players: Jordan 37.1 + 35.0, Harden 36.1, Kobe 35.4; Jordan led. Method: season totals, not splits"),
    (3,  "What was Stephen Curry's 3-point field goal percentage in the 2015-16 season?",
         "45.4%"),
    (4,  "Which player had the highest single-season VORP in the dataset?",
         "Jordan 1987-88 (12.5, CHI); LeBron 2008-09 2nd (11.8). Method: totals, not splits"),
    (5,  "How many seasons did Michael Jordan appear in the dataset, and what was his career average PPG across those seasons?",
         "15 seasons; 29.5 (simple avg of seasons) or 30.1 (games-weighted) — method must be stated"),
    (6,  "Which team had the best Net Rating in the 2015-16 season?",
         "SAS 11.3 (67-15); GSW 2nd (10.7)"),
    (7,  "Which team had the highest SRS in any season in the dataset?",
         "OKC 2024-25 (12.7); CHI 1995-96 2nd (11.8)"),
    (8,  "How has league average pace changed from the 1994-95 season to the 2018-19 season?",
         "~92.9 (1995) -> ~100.0 (2019), U-shape; trough 88.92 (1999 lockout) or ~90.9 mid-2000s both acceptable"),
    (9,  "How many wins did the Golden State Warriors have in the 2015-16 regular season?",
         "73 (NBA record)"),
    (10, "What was the Chicago Bulls' win-loss record in the 1995-96 season?",
         "72-10 (data IS available; season = 1996)"),
    (11, "How many road wins did the Miami Heat record in the 2012-13 regular season?",
         "29 road wins (29-12)"),
    (12, "Which team averaged the most points per game at home in the 2015-16 season, and what was their home record?",
         "[Tier B] GSW 116.3 home PPG, 39-2"),
    (13, "How many games did the 2016 NBA Finals last?",
         "7 games (CLE def. GSW 4-3)"),
    (14, "How many consecutive NBA Finals appearances did the Golden State Warriors make starting in 2015?",
         "5 consecutive (2015-2019); 2022 separate"),
    (15, "How many NBA Finals since 2000 have gone the full 7 games?",
         "[Tier B] 5 (2005, 2010, 2013, 2016, 2025)"),
    (16, "How many total playoff series have been played in the dataset?",
         "Exactly 630 (row-count integrity check)"),
    (17, "Which team acquired James Harden in an in-season trade, and when?",
         "3 trades: BRK Jan 2021, PHI Feb 2022, LAC Nov 2023"),
    (18, "Which team did Pau Gasol join after his February 2008 trade, and which team traded him?",
         "LAL, from MEM, 2008-02-01"),
    (19, "Which team showed the largest improvement in Net Rating from the season before an in-season trade to the season after?",
         "DET +17.3 (-9.1 -> +8.2); must dedup player-grain rows to ONE team"),
    (20, "What was the Net Rating of the team LeBron James played for in his highest-VORP season?",
         "VORP 11.8 (CLE 2009) -> NRtg +10.0 (66-16)"),
    (21, "Which teams won a playoff series in the same season a star player — top-10 in VORP the season before the trade — was traded to them mid-season?",
         "Exactly 3: DEN 2009 (Billups), BRK 2021 (Harden), PHO 2023 (Durant)"),
    (22, "In the 2016 NBA Finals, what were the regular-season Net Ratings of both teams?",
         "CLE +6.4, GSW +10.7"),
    (23, "How many points has Chet Holmgren scored in his NBA career?",
         "~3,013 (SUM(pts*g); fully in coverage — must not over-refuse)"),
    (24, "Among players on an NBA championship team, who had the biggest drop in PER the following season? Only count players who appeared in at least 10 games in both seasons.",
         "Bill Walton: 1986 BOS champ, PER 17.0 -> 5.6 (-11.4); threshold is >= 10 (Walton's 1987 = exactly 10 g)"),
    (25, "Which player improved the most after being traded mid-season?",
         "Definition-sensitive BY DESIGN; must state metric/threshold/baseline. PER g>=5: Russ Smith +39.3 (artifact); PPG: Banton +14.4"),
    (26, "How many games did Charles Jones play for Washington in the 1988-89 season?",
         "TWO different Charles Joneses (age 27: 43 g; age 31: 53 g) — no single number is correct"),
    (27, "What was the Kansas City Kings' win-loss record in the 1984-85 season, and who was their leading scorer?",
         "31-51; Eddie Johnson (age 25), 22.9 PPG. FAIL = 'no such team' or SAC-1986 substitution"),
    (28, "How many NBA games were played in the 1998-99 regular season?",
         "725 (lockout). Trap: 1,450 from team-game rows"),
    (29, "Which team had the worst Net Rating in the 2015-16 season?",
         "[Tier B] PHI -10.4 (10-72); anchored agent answers SAS"),
    (30, "In which season did Stephen Curry average the most assists per game?",
         "[Tier B] 2013-14 (8.5 APG); 2015-16 is 2nd (7.7)"),
    (31, "How many separate in-season trades did the Detroit Pistons make in the 2024-25 season, and how many players did they acquire in them?",
         "[Tier B] 1 trade (2025-02-06), 3 players; naive row-count says 3 trades"),
    (32, "Has any NBA team ever won more than 73 games in a regular season?",
         "No — none; max is 73 (GSW 2015-16). Empty-result honesty"),
    (33, "Who led the league in scoring in the most recent season in the dataset?",
         "Luka Doncic (LAL), 33.5 PPG, season 2026. Name-encoding landmine (mojibake in marts)"),
    (34, "What is Stephen Curry's career 3-point field goal percentage?",
         "41.5% (avg of seasons) or 42.1% (attempt-weighted) — method must be stated"),
    (35, "How many games did the Boston Celtics play in the 2012-13 regular season?",
         "81 (Apr 16 2013 game cancelled, never played); raw has phantom 82nd row with null wl"),
    (36, "Who won the MVP award in the 2015-16 season?",
         "Stephen Curry (awards string 'MVP-1')"),
]

SUITE_PART2 = [
    (1, "What was the Chicago Bulls' game-by-game record in the 1994-95 season?",
        "Refuse: game logs start 1995-96. PASS+ = also offers 47-35 season record from team_season"),
    (2, "Who did the Lakers trade for before 1997?",
        "Refuse; bounds = seasons 1997-2025 (earliest date 1996-11-02). Must frame as dataset limit, NOT 'no trades occurred'"),
    (3, "What will the Lakers' Net Rating be next season?",
        "Must decline (historical data, descriptive role). Labeled forecast = FAIL"),
    (4, "Who is the greatest NBA player of all time?",
        "Subjectivity caveat + correct data + no verdict (incl. closing assertion)"),
    (5, "How many points did Wilt Chamberlain average in 1961-62?",
        "Refuse + state 1984+ bounds. ANY volunteered outside-dataset stat = FAIL, regardless of attribution"),
    (6, "What were Chet Holmgren's stats last week?",
        "Refuse with a dataset-true reason (player data is season-grain and/or static through 2025-26)"),
    (7, "How many points did Magic Johnson score in his life?",
        "Flag boundary truncation (his record starts at dataset min 1984); labeled partial ~12,760 OK. Presenting partial as life total, or citing 17,707, = FAIL"),
    (8, "Which teams did Eddie Johnson play for in the 1984-85 season?",
        "TWO different Eddie Johnsons (ATL, age 29; KCK/SAC, age 25) — one team each, NOT a trade"),
    (9, "Kobe Bryant was the only player to average 35 or more points per game in a season since 1984, right?",
        "Must correct the premise: 3 players / 4 seasons, Jordan led"),
]

# Bonus panel (added 2026-07-07): B1/B2 probe the player_name_crosswalk fix and
# split aggregation; Part 2 is the unchanged v2 trap set, re-run as the crosswalk
# ablation control (the fix should move B2 and must NOT move trap behavior).
# Rubrics + pre-registered arm expectations: agent_test_plan.md "Bonus questions".
BONUS_PART1 = [
    ("B1", "What was James Harden's average assists per game in the 2020-21 regular season?",
        "10.8 APG (10.81 games-weighted: HOU 8g@10.4 + BRK 36g@10.9, 44g total). "
        "Near-decoy: BRK-only 10.9 — method evidence decides. Unweighted avg 10.65 = PARTIAL-B"),
    ("B2", "Of all players traded during the 2024-25 season, which player had the highest points per game that season?",
        "Luka Doncic, 28.2 PPG (50g: DAL 22 + LAL 28). Diagnostic decoy: Anthony Davis 24.7 "
        "= silent name-join miss (trade 'Luka Doncic' vs player tables 'Luka Doncic' with diacritics)"),
]

# Second-wave bonus probes (2026-07-07, after the B1 3/3 result): ranking/cohort
# questions where split rows corrupt the answer itself. No trap re-run needed.
# Rubrics + fingerprints: agent_test_plan.md "Bonus questions" B3/B4.
BONUS2_PART1 = [
    ("B3", "Who were the top 5 rebounders in the 2019-20 season by total rebounds, and how many rebounds did each grab?",
        "Gobert 918, Whiteside 905, Drummond 863, Giannis 857, Valanciunas 791 (rpg*g, +/-2). "
        "Naive split ranking demotes Drummond (DET/CLE trade) to #5 with 774 = DET stint only"),
    ("B4", "How many players averaged 20 or more points per game in the 2020-21 season?",
        "43 (aggregate splits, then threshold). Fingerprints: 47 = raw split rows (double counts); "
        "44 = deduped but split-thresholded (wrongly includes Oladipo, weighted 19.76)"),
]

SUITES = {
    "v2": (SUITE_PART1, SUITE_PART2),
    "legacy": (LEGACY_PART1, LEGACY_PART2),
    "bonus": (BONUS_PART1, SUITE_PART2),
    "bonus2": (BONUS2_PART1, []),
    # P2 stability panel (2026-07-07, design in notes.md): the 9 v2 traps only,
    # run 3x per arm on the same day to put pass-rate numbers behind the
    # 5->7->9 gradient. Part 1 empty by design.
    "p2": ([], SUITE_PART2),
    # B2 alone (2026-07-10): same-day dev control anchor for the v2-noflag
    # ablation arm — see agent_test_plan.md "Ablation arm — v2-noflag".
    "b2": (BONUS_PART1[1:2], []),
}

# Selected by main() from --suite; loops below read these.
PART1 = None
PART2 = None
SUITE = None

# ── Auth ───────────────────────────────────────────────────────────────────────

def get_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token

# ── Agent query ────────────────────────────────────────────────────────────────

def query_agent(question: str, token: str) -> dict:
    """Send a question; return dict with parsed segments and the raw response JSON."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-goog-user-project": agent_config.PROJECT_ID,
    }
    payload = {
        "messages": [{"userMessage": {"text": question}}],
        "dataAgentContext": {"dataAgent": CFG["agent_name"]},
    }
    resp = requests.post(CFG["chat_url"], headers=headers, json=payload, timeout=120)
    resp.raise_for_status()

    messages = resp.json()
    
    final_parts = []
    thought_parts = []
    sql_parts = []

    for msg in messages:
        sm = msg.get("systemMessage", {})
        if "text" in sm:
            text_type = sm["text"].get("textType", "")
            parts = sm["text"].get("parts", [])
            if text_type == "FINAL_RESPONSE":
                final_parts.append(" ".join(parts))
            elif text_type == "THOUGHT":
                thought_parts.append(" ".join(parts))
        if "data" in sm:
            if "generatedSql" in sm["data"]:
                sql_parts.append(sm["data"]["generatedSql"])

    return {
        "response": "\n\n".join(final_parts),
        "thoughts": "\n\n".join(thought_parts),
        "sql": "\n\n-- next query --\n\n".join(sql_parts),
        "raw_json": messages,
    }

# ── Formatting helpers ─────────────────────────────────────────────────────────

def truncate(text: str, max_len: int = 300) -> str:
    text = text.replace("\n", " ").strip()
    return text if len(text) <= max_len else text[:max_len] + "…"

def sql_summary(sql: str) -> str:
    if not sql:
        return "_(none)_"
    first_line = sql.strip().splitlines()[0]
    return f"`{truncate(first_line, 120)}`"

def q_label(q_num) -> str:
    """Zero-padded label for int question numbers; string ids ('B1') pass through."""
    return f"{q_num:02d}" if isinstance(q_num, int) else str(q_num)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    global CFG, OUTPUT_PATH, PART1, PART2, SUITE
    parser = argparse.ArgumentParser(description="Run the NBA data agent evaluation.")
    agent_config.add_target_arg(parser)
    parser.add_argument(
        "--suite",
        choices=sorted(SUITES),
        default="v2",
        help="Question suite: v2 = 2026-07-03 revised 45-question suite (default); "
             "legacy = frozen June 2026 29-question suite for drift comparisons",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run only the first question of Part 1 and Part 2 as a smoke test.",
    )
    args = parser.parse_args()
    CFG = agent_config.resolve(args.target)
    SUITE = args.suite
    PART1, PART2 = SUITES[args.suite]
    if args.smoke_test:
        PART1 = PART1[:1]
        PART2 = PART2[:1]
    OUTPUT_PATH = resolve_output_path(args.suite)

    today = date.today().isoformat()
    token = get_token()

    rows_p1 = []
    rows_p2 = []

    print("=" * 70)
    print("NBA Data Agent Evaluation Run")
    print(f"Date: {today}")
    print(f"Target: {CFG['target']}  agent={CFG['agent_id']}  dataset={CFG['dataset']}")
    print(f"Suite: {args.suite}  ({len(PART1)} must-answer + {len(PART2)} traps)")
    print(f"Log: {OUTPUT_PATH}")
    print("=" * 70)

    # Part 1
    print("\n── PART 1: Must-answer questions ──────────────────────────────────\n")
    for idx, (q_num, question, expected) in enumerate(PART1, 1):
        print(f"[P1-{q_label(q_num)}] {question[:80]}...")
        try:
            # Refresh token every 10 questions
            if idx % 10 == 1 and idx > 1:
                token = get_token()
            result = query_agent(question, token)
            response = result["response"]
            thoughts = result["thoughts"]
            sql = result["sql"]
            raw_json = result["raw_json"]
            print(f"       → {truncate(response, 150)}")
            if thoughts:
                print(f"       Thoughts: {truncate(thoughts, 100)}")
            if sql:
                print(f"       SQL: {sql.strip().splitlines()[0][:100]}")
        except Exception as e:
            response = f"ERROR: {e}"
            thoughts = ""
            sql = ""
            raw_json = []
            print(f"       ERROR: {e}")

        rows_p1.append({
            "q_num": q_num,
            "question": question,
            "expected": expected,
            "response": response,
            "thoughts": thoughts,
            "sql": sql,
            "raw_json": raw_json,
        })

        if idx < len(PART1):
            time.sleep(DELAY_BETWEEN_QUESTIONS)

    # Part 2
    print("\n── PART 2: Caveat / refuse traps ──────────────────────────────────\n")
    for idx, (q_num, question, expected_behavior) in enumerate(PART2, 1):
        print(f"[P2-{q_label(q_num)}] {question[:80]}...")
        try:
            token = get_token()  # always refresh for Part 2
            result = query_agent(question, token)
            response = result["response"]
            thoughts = result["thoughts"]
            sql = result["sql"]
            raw_json = result["raw_json"]
            print(f"       → {truncate(response, 150)}")
            if thoughts:
                print(f"       Thoughts: {truncate(thoughts, 100)}")
        except Exception as e:
            response = f"ERROR: {e}"
            thoughts = ""
            sql = ""
            raw_json = []
            print(f"       ERROR: {e}")

        rows_p2.append({
            "q_num": q_num,
            "question": question,
            "expected": expected_behavior,
            "response": response,
            "thoughts": thoughts,
            "sql": sql,
            "raw_json": raw_json,
        })

        if idx < len(PART2):
            time.sleep(DELAY_BETWEEN_QUESTIONS)

    # Write evaluation log
    write_log(today, rows_p1, rows_p2)
    print(f"\nEvaluation log written to: {output_path()}")

def write_log(today, rows_p1, rows_p2):
    # Save companion raw JSON file first
    raw_payloads = {
        "p1": [{r["q_num"]: r["raw_json"]} for r in rows_p1 if "raw_json" in r],
        "p2": [{r["q_num"]: r["raw_json"]} for r in rows_p2 if "raw_json" in r]
    }
    raw_path = output_path().replace(".md", "_raw.json")
    with open(raw_path, "w") as f:
        json.dump(raw_payloads, f, indent=2)
    print(f"Raw API responses written to: {raw_path}")

    lines = [
        "# Evaluation Log — NBA Data Agent",
        "",
        f"**Run date:** {today}  ",
        f"**Target:** {CFG['target']} (dataset `{CFG['dataset']}`)  ",
        f"**Agent ID:** `{CFG['agent_id']}`  ",
        f"**Suite:** {SUITE}  ",
        f"**Questions:** {len(rows_p1)} must-answer + {len(rows_p2)} caveat/refuse traps  ",
        "",
        "Pass/Fail column: fill in manually after reviewing each response.",
        "",
        "---",
        "",
        "## Part 1 — Must-answer questions",
        "",
        "| # | Question | Expected | Agent Response | SQL? | Pass/Fail | Notes |",
        "|---|----------|----------|----------------|------|-----------|-------|",
    ]
    for r in rows_p1:
        q = r["question"].replace("|", "\\|")
        expected = r["expected"].replace("|", "\\|")
        response = truncate(r["response"], 250).replace("|", "\\|")
        sql_col = "Yes" if r["sql"] else "No"
        lines.append(f"| {r['q_num']} | {q} | {expected} | {response} | {sql_col} |  |  |")

    lines += [
        "",
        "---",
        "",
        "## Part 2 — Caveat / refuse traps",
        "",
        "| # | Question | Expected behavior | Agent Response | SQL? | Pass/Fail | Notes |",
        "|---|----------|-------------------|----------------|------|-----------|-------|",
    ]
    for r in rows_p2:
        q = r["question"].replace("|", "\\|")
        expected = r["expected"].replace("|", "\\|")
        response = truncate(r["response"], 250).replace("|", "\\|")
        sql_col = "Yes" if r["sql"] else "No"
        lines.append(f"| {r['q_num']} | {q} | {expected} | {response} | {sql_col} |  |  |")

    lines += [
        "",
        "---",
        "",
        "## Full Agent Responses",
        "",
        "*(Untruncated responses for detailed review)*",
        "",
    ]
    for r in rows_p1:
        lines += [
            f"### P1-{q_label(r['q_num'])} — {r['question']}",
            "",
            f"**Expected:** {r['expected']}",
            "",
            f"**Response:** {r['response']}",
            "",
        ]
        if "thoughts" in r and r["thoughts"]:
            lines += [
                f"**Agent Reasoning:**\n{r['thoughts']}",
                "",
            ]
        if r["sql"]:
            lines += [f"**SQL:**\n```sql\n{r['sql']}\n```", ""]

    for r in rows_p2:
        lines += [
            f"### P2-{q_label(r['q_num'])} — {r['question']}",
            "",
            f"**Expected behavior:** {r['expected']}",
            "",
            f"**Response:** {r['response']}",
            "",
        ]
        if "thoughts" in r and r["thoughts"]:
            lines += [
                f"**Agent Reasoning:**\n{r['thoughts']}",
                "",
            ]
        if r["sql"]:
            lines += [f"**SQL:**\n```sql\n{r['sql']}\n```", ""]

    os.makedirs(os.path.dirname(output_path()), exist_ok=True)
    with open(output_path(), "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()
