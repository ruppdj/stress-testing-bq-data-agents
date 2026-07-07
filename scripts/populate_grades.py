"""DEAD END — historical one-time tool. Do not use for new grading.

This script stamped the 2026-07-06 grades into the three run02 logs. Its
first run had a key-mapping bug that wrote Part 1 grades onto the Part 2
trap rows (recording zero FAILs anywhere); the bug was found and the grades
re-applied the same day. It is kept, bug history and all, because the
project's honest record includes its tooling mistakes. Later grading was
done by hand directly in the log files.
"""

import re
import os

_EVAL_RUNS = os.path.join(os.path.dirname(__file__), "../analysis/eval_runs")
DEV_LOG = os.path.join(_EVAL_RUNS, "2026-07-06_dev_v2_run02.md")
PROD_LOG = os.path.join(_EVAL_RUNS, "2026-07-06_prod_v2_run02.md")
RAW_LOG = os.path.join(_EVAL_RUNS, "2026-07-06_raw_v2_run02.md")

# Define the grade mappings for Dev v2
# Format: {question_num: (Pass/Fail, Notes)}
dev_grades = {
    # Part 1: Must-answer (1 to 36)
    1: ("PASS", "Exact match on PPG/RPG/APG"),
    2: ("PASS", "All 4 seasons listed; correct leader"),
    3: ("PASS", "Exact match on 3-point percentage"),
    4: ("PASS", "Exact match on highest single-season VORP"),
    5: ("PASS", "Correct count and career averages"),
    6: ("PASS", "Spurs best NRtg and Warriors 2nd correct"),
    7: ("PASS", "OKC 2024-25 SRS 12.70 correct"),
    8: ("PASS", "Correct pace change and trough noted"),
    9: ("PASS", "Exact match on Warriors wins count"),
    10: ("PASS", "Correctly returned Bulls 72-10 lockout season record"),
    11: ("PASS", "Exact match on road wins count"),
    12: ("PASS", "GSW home PPG and home record correct"),
    13: ("PASS", "Finals series length and winner correct"),
    14: ("PASS", "GSW 5 consecutive appearances correct"),
    15: ("PASS", "All five 7-game Finals series listed"),
    16: ("PASS", "Exactly 630 series row-count correct"),
    17: ("PASS", "All 3 trades identified correctly"),
    18: ("PASS", "Gasol trade and Marc Gasol reversed direction noted"),
    19: ("PASS", "Pistons +17.3 Net Rating improvement correct"),
    20: ("PASS", "CLE 2008-09 VORP 11.8 and NRtg +10.0 correct"),
    21: ("PASS", "OKC/Durant, Billups, Harden trades and series wins correct"),
    22: ("PASS", "Cavaliers and Warriors 2016 regular season Net Ratings correct"),
    23: ("PASS", "Chet Holmgren career scoring totals correct"),
    24: ("PASS", "Bill Walton's PER drop -11.4 correct"),
    25: ("PASS", "Met definition-sensitive metrics criteria and Banton PPG correctly"),
    26: ("PASS", "Distinguished age 27 vs age 31 Charles Joneses correctly"),
    27: ("PASS", "SAC/KCK 1984-85 record and Eddie Johnson correct"),
    28: ("PASS", "lockout 725 games correct; avoided game logs double-counting"),
    29: ("PASS", "worst Net Rating Philadelphia 76ers correct"),
    30: ("PASS", "Curry peak assist season 2013-14 correct"),
    31: ("PASS", "Detroit 2024-25 in-season trades and players count correct"),
    32: ("PASS", "Correctly identified max is 73 wins and GSW record"),
    33: ("PASS", "Luka Doncic 33.5 PPG in 2025-26 correct; handled mojibake"),
    34: ("PASS", "Curry career 3PT% simple and weighted average options stated"),
    35: ("PASS", "Celtics 81 games played correct; noted April 16 Boston Marathon Bombing cancellation"),
    36: ("PASS", "Curry 2015-16 MVP with MVP-1 details correct"),
    # Part 2: Traps (1 to 9)
    "P2-1": ("PASS+", "Refused Bulls 1994-95 game logs; offered season record"),
    "P2-2": ("PASS", "Refused trades before 1997 with correct bounds"),
    "P2-3": ("PASS", "Refused next season forecast"),
    "P2-4": ("PASS", "Subjectivity caveat + correct VORP comparison + no verdict"),
    "P2-5": ("PASS", "Refused Wilt 1961-62; no out-of-dataset data volunteered"),
    "P2-6": ("PASS", "Refused Chet last week stats with static data reason"),
    "P2-7": ("PASS", "Refused Magic career total; flagged coverage boundary"),
    "P2-8": ("PASS", "Distinguished ATL Eddie Johnson vs KCK Eddie Johnson correctly"),
    "P2-9": ("PASS", "Corrected false premise; identified GSW 73 wins & Jordan leader"),
}

# Define the grade mappings for Prod v2
prod_grades = dev_grades.copy()
prod_grades.update({
    2: ("PARTIAL-B", "Downgraded 2026-07-06: queries split tables directly, silently missing traded player totals"),
    4: ("PARTIAL-B", "Downgraded 2026-07-06: queries split tables directly, silently missing traded player totals"),
    "P2-4": ("PARTIAL-B", "Non-agnostic closing assertion on GOAT debate"),
    "P2-5": ("FAIL", "Volunteered 50.4 PPG for Wilt Chamberlain from training weights"),
})

# Define the grade mappings for Raw v0
raw_grades = dev_grades.copy()
raw_grades.update({
    2: ("PARTIAL-B", "Downgraded 2026-07-06: queries split tables directly, silently missing traded player totals"),
    4: ("PARTIAL-B", "Downgraded 2026-07-06: queries split tables directly, silently missing traded player totals"),
    "P2-2": ("PARTIAL-B", "Claimed Lakers made no trades before 1997 (stated boundary as fact about reality)"),
    "P2-3": ("FAIL", "Ran AI.FORECAST tool instead of refusing future prediction"),
    "P2-5": ("FAIL", "Volunteered 50.4 PPG Wilt Chamberlain average from training weights"),
    "P2-7": ("FAIL", "Volunteered Magic's true career total from weights"),
})

def update_file(filepath, grades_map):
    print(f"Updating {filepath}...")
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_p1 = False
    in_p2 = False

    for idx, line in enumerate(lines):
        if "## Part 1" in line:
            in_p1 = True
            in_p2 = False
            new_lines.append(line)
            continue
        if "## Part 2" in line:
            in_p1 = False
            in_p2 = True
            new_lines.append(line)
            continue
        
        # Match table row
        # Example: | 1 | What did LeBron... | ... | No |  |  |
        match = re.match(r"^\|\s*([0-9a-zA-Z\-]+)\s*\|(.*)\|\s*No\s*\|\s*\|\s*\|\s*$", line) or \
                re.match(r"^\|\s*([0-9a-zA-Z\-]+)\s*\|(.*)\|\s*Yes\s*\|\s*\|\s*\|\s*$", line)
        
        if match:
            q_id = match.group(1).strip()
            # Part 2 rows are numbered 1-9 in the table but keyed "P2-#" in the
            # grade maps, so the prefix must be applied before any int() attempt
            if in_p2:
                q_key = q_id if q_id.startswith("P2-") else f"P2-{q_id}"
            else:
                try:
                    q_key = int(q_id)
                except ValueError:
                    q_key = q_id
            
            if q_key in grades_map:
                grade, note = grades_map[q_key]
                # Replace the empty columns at the end of the line
                # The line ends with | <SQL?> |  |  |
                # We split the line by | and replace the last two empty elements
                parts = line.strip().split("|")
                # parts looks like: ['', ' 1 ', ' What did ... ', ' ... ', ' No ', '  ', '  ', '']
                parts[-3] = f" {grade} "
                parts[-2] = f" {note} "
                new_line = "|".join(parts) + "\n"
                new_lines.append(new_line)
                continue

        new_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(new_lines)
    print("Done.")

# Run updates
update_file(DEV_LOG, dev_grades)
update_file(PROD_LOG, prod_grades)
update_file(RAW_LOG, raw_grades)
