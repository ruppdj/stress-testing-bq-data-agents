"""Create a Conversational Analytics data agent for a target that doesn't have one.

Creates the agent shell with its BigQuery datasource references only; the
published context (instructions, example queries, glossary) is uploaded
separately with upload_nba_agent.py --target <target>. After a successful
create, record the printed agent ID in scripts/agent_config.py.
"""

import argparse
import json
import time

import google.auth
import google.auth.transport.requests
import requests

import agent_config


def get_token():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


def main():
    parser = argparse.ArgumentParser(description="Create a data agent for a target.")
    agent_config.add_target_arg(parser)
    parser.add_argument("--agent-id", required=True,
                        help="ID for the new agent (e.g. nba-dev-agent-v2)")
    args = parser.parse_args()

    cfg = agent_config.TARGETS[args.target]
    if cfg["agent_id"] is not None:
        raise SystemExit(
            f"Target '{args.target}' already has agent_id {cfg['agent_id']} in "
            "agent_config.py — refusing to create a duplicate."
        )

    dataset = cfg["dataset"]
    table_refs = [
        {"projectId": agent_config.PROJECT_ID, "datasetId": dataset, "tableId": t}
        for t in cfg["tables"]
    ]
    published_context = {
        "datasourceReferences": {"bq": {"tableReferences": table_refs}}
    }
    # The raw (v0 baseline) target gets its minimal instruction at create time;
    # dev/prod get theirs via upload_nba_agent.py.
    if cfg.get("system_instruction"):
        published_context["systemInstruction"] = cfg["system_instruction"]
    body = {
        "displayName": f"nba-{args.target}-agent ({dataset})",
        "description": f"NBA data agent for the {args.target} target, reading {dataset}.",
        "dataAnalyticsAgent": {"publishedContext": published_context},
    }

    headers = {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "x-goog-user-project": agent_config.PROJECT_ID,
    }
    url = (
        f"{agent_config.API_BASE}/projects/{agent_config.PROJECT_ID}"
        f"/locations/{agent_config.LOCATION}/dataAgents?data_agent_id={args.agent_id}"
    )
    print(f"POST {url}")
    print(f"Datasources: {dataset} — {len(table_refs)} tables")
    print(f"System instruction at create: {'yes' if 'systemInstruction' in published_context else 'no'}")
    resp = requests.post(url, headers=headers, json=body)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code != 200:
        print("Response:", resp.text)
        raise SystemExit(1)

    op = resp.json()
    # Create returns a long-running operation; poll until done.
    while op.get("name", "").find("/operations/") != -1 and not op.get("done"):
        time.sleep(2)
        poll = requests.get(f"{agent_config.API_BASE}/{op['name']}", headers=headers)
        poll.raise_for_status()
        op = poll.json()

    if op.get("error"):
        print("Operation failed:", json.dumps(op["error"], indent=2))
        raise SystemExit(1)

    print(json.dumps(op, indent=2))
    print(f"\nSUCCESS. Record in scripts/agent_config.py under '{args.target}': "
          f"\"agent_id\": \"{args.agent_id}\"")


if __name__ == "__main__":
    main()
