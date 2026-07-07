import argparse
import google.auth
import google.auth.transport.requests
import requests
import json
import os
import re

import agent_config

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json_queries_path = os.path.join(REPO_ROOT, "analysis", "verified_queries.json")
instructions_path = os.path.join(REPO_ROOT, "analysis", "agent_instructions.md")

def get_token():
    credentials, project = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token

def extract_system_instructions():
    if not os.path.exists(instructions_path):
        return None
    with open(instructions_path, 'r') as f:
        content = f.read()

    match = re.search(r'## Instructions \(paste into Console\)\s*```\s*(.*?)\s*```', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def main():
    parser = argparse.ArgumentParser(description="Upload published context to the NBA data agent.")
    agent_config.add_target_arg(parser)
    args = parser.parse_args()
    if args.target == "raw":
        raise SystemExit(
            "Refusing --target raw: the v0 baseline agent must not receive the "
            "curated grounding package (instructions/glossary/verified queries). "
            "Its minimal system instruction is set at create time by create_agent.py."
        )
    cfg = agent_config.resolve(args.target)
    print(f"TARGET: {cfg['target'].upper()}  agent={cfg['agent_id']}  dataset={cfg['dataset']}")

    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if not os.path.exists(json_queries_path):
        print(f"Error: {json_queries_path} not found.")
        return
    with open(json_queries_path, 'r') as f:
        queries = json.loads(agent_config.rewrite_dataset(f.read(), cfg))

    system_instruction = extract_system_instructions()
    if not system_instruction:
        print("Error: Could not extract system instructions.")
        return
    system_instruction = agent_config.rewrite_dataset(system_instruction, cfg)
        
    example_queries = []
    for q in queries:
        example_queries.append({
            "naturalLanguageQuestion": q["question"],
            "sqlQuery": q["sql"]
        })
        
    glossary_terms = [
        {
            "displayName": "VORP",
            "description": "Value Over Replacement Player. Cumulative metric in mart_player_season_totals estimating points contributed above a replacement-level player. Context: 3+ is a solid starter, 6+ is All-Star level, 10+ is historic.",
            "labels": ["Value Over Replacement Player", "replacement value", "player value"]
        },
        {
            "displayName": "BPM",
            "description": "Box Plus/Minus. A box score-based metric in mart_player_season_totals measuring a player's per-100-possession performance relative to league average (0.0). Context: 5+ is All-Star level, 8+ is MVP level.",
            "labels": ["Box Plus Minus", "plus-minus", "player efficiency"]
        },
        {
            "displayName": "Win Shares",
            "description": "WS. Estimated wins contributed by a player in mart_player_season_totals. Context: 5-8 is starter, 10+ is All-Star, 15+ is MVP level.",
            "labels": ["WS", "wins contributed", "player wins"]
        },
        {
            "displayName": "Net Rating",
            "description": "NRtg. The difference between a team's offensive rating and defensive rating. Best overall team strength indicator. Represented by nrtg in mart_team_season or nrtg_yr0/yr1 in mart_trade_impact.",
            "labels": ["NRtg", "net efficiency", "point differential per 100 possessions"]
        },
        {
            "displayName": "SRS",
            "description": "Simple Rating System. Margin of victory adjusted for strength of schedule in mart_team_season.",
            "labels": ["Simple Rating System", "team rating", "strength rating"]
        },
        {
            "displayName": "Pace",
            "description": "tempo. Estimated possessions per 48 minutes in mart_team_season.",
            "labels": ["tempo", "game speed", "possessions"]
        },
        {
            "displayName": "Traded Player",
            "description": "TOT / TRD. Mid-season traded players have their season aggregate stats in rows where team_abbrev = 'TRD' and is_traded_player = true. Individual team splits have is_traded_player = false.",
            "labels": ["TRD", "TOT", "mid-season trade totals"]
        },
        {
            "displayName": "Game Record",
            "description": "regular season record. Team records come from mart_game_logs (one row per team per game). For league-wide game counts or unique match results use mart_unique_games (one row per physical game); for league-wide counting-stat aggregates filter mart_game_logs to is_home = true to avoid double-counting.",
            "labels": ["regular season record", "wins and losses", "win-loss"]
        },
        {
            "displayName": "Franchise Lineage",
            "description": "Team identity follows the NBA's official franchise records lineage (Basketball-Reference convention). Relocated teams keep one canonical abbreviation across the move (SEA→OKC, VAN→MEM, NJN→BRK, KCK→SAC, SDC→LAC, WSB→WAS); era-correct team names per season are in mart_team_season.team. The one records-vs-physical divergence is Charlotte/New Orleans: the 1989–2002 Charlotte Hornets records belong to the modern Charlotte franchise (CHO, including the 2005–2014 Bobcats era), and the New Orleans lineage (NOP, including the NOH/NOK Hornets years) begins 2002-03. Questions about the physical organization that moved to New Orleans in 2002 cannot be answered from team identifiers — state this caveat rather than silently answering under the records lineage.",
            "labels": ["franchise history", "relocation", "team lineage", "Hornets", "Pelicans", "SuperSonics"]
        }
    ]
    
    patch_body = {
        "dataAnalyticsAgent": {
            "publishedContext": {
                "systemInstruction": system_instruction,
                "exampleQueries": example_queries,
                "glossaryTerms": glossary_terms,
                "options": {
                    "datasource": {
                        "bigQueryMaxBilledBytes": "1073741824"
                    }
                }
            }
        }
    }
    
    # updateMask deliberately excludes datasourceReferences so the agent's
    # data source connections are preserved
    url = f"{agent_config.API_BASE}/{cfg['agent_name']}?updateMask=dataAnalyticsAgent.publishedContext.exampleQueries,dataAnalyticsAgent.publishedContext.systemInstruction,dataAnalyticsAgent.publishedContext.glossaryTerms,dataAnalyticsAgent.publishedContext.options"
    print(f"PATCH {url}")
    response = requests.patch(url, headers=headers, json=patch_body)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS! Verified queries, system instructions, glossary terms, and options limits uploaded.")
    else:
        print("Response:", response.text)

if __name__ == "__main__":
    main()
