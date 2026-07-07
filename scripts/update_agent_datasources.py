"""Sync a target's live agent datasource references to scripts/agent_config.py.

Used when an agent must be repointed at a different dataset (e.g. the
2026-07-03 v0 repoint from nba_raw to the frozen nba_raw_ground_zero).
agent_config.py is the source of truth; this PATCHes the live agent to match.
The updateMask covers ONLY datasourceReferences, so system instructions,
example queries, and glossary terms are untouched by construction.
"""

import argparse
import json

import google.auth
import google.auth.transport.requests
import requests

import agent_config


def get_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def current_datasets(agent: dict) -> list:
    refs = (agent.get("dataAnalyticsAgent", {})
                 .get("publishedContext", {})
                 .get("datasourceReferences", {})
                 .get("bq", {})
                 .get("tableReferences", []))
    return sorted({r["datasetId"] for r in refs})


def main():
    parser = argparse.ArgumentParser(
        description="PATCH a target's agent datasources to match agent_config.py.")
    agent_config.add_target_arg(parser)
    args = parser.parse_args()
    cfg = agent_config.resolve(args.target)

    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "x-goog-user-project": agent_config.PROJECT_ID,
    }
    agent_url = f"{agent_config.API_BASE}/{cfg['agent_name']}"

    before = requests.get(agent_url, headers=headers)
    before.raise_for_status()
    print(f"Agent:  {cfg['agent_id']}")
    print(f"Before: reads {current_datasets(before.json())}")
    print(f"Config: wants ['{cfg['dataset']}'] — {len(cfg['tables'])} tables")

    table_refs = [
        {"projectId": agent_config.PROJECT_ID, "datasetId": cfg["dataset"], "tableId": t}
        for t in cfg["tables"]
    ]
    patch_body = {
        "dataAnalyticsAgent": {
            "publishedContext": {
                "datasourceReferences": {"bq": {"tableReferences": table_refs}}
            }
        }
    }
    url = f"{agent_url}?updateMask=dataAnalyticsAgent.publishedContext.datasourceReferences"
    print(f"PATCH {url}")
    resp = requests.patch(url, headers=headers, json=patch_body)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code != 200:
        print("Response:", resp.text)
        raise SystemExit(1)

    after = requests.get(agent_url, headers=headers)
    after.raise_for_status()
    got = current_datasets(after.json())
    print(f"After:  reads {got}")
    if got != [cfg["dataset"]]:
        print("MISMATCH — agent datasets do not match config; inspect manually:")
        print(json.dumps(after.json(), indent=2))
        raise SystemExit(1)
    print("SUCCESS. Agent datasources match agent_config.py.")


if __name__ == "__main__":
    main()
