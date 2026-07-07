import yaml
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
marts_yml_path = os.path.join(REPO_ROOT, "solution", "dbt", "sports_analytics", "models", "marts", "marts.yml")
md_output_path = os.path.join(REPO_ROOT, "analysis", "verified_queries_list.md")
json_output_path = os.path.join(REPO_ROOT, "analysis", "verified_queries.json")

def main():
    if not os.path.exists(marts_yml_path):
        print(f"Error: {marts_yml_path} does not exist.")
        return

    with open(marts_yml_path, 'r') as f:
        data = yaml.safe_load(f)

    models = data.get('models', [])
    extracted = []

    for model in models:
        model_name = model.get('name')
        meta = model.get('config', {}).get('meta', {})
        verified_queries = meta.get('verified_queries', [])
        
        for q in verified_queries:
            extracted.append({
                "model": model_name,
                "question": q.get('question').strip(),
                "sql": q.get('sql').strip()
            })

    # Write Markdown output
    with open(md_output_path, 'w') as f:
        f.write("# Verified Queries Reference List\n\n")
        f.write("Use this file to easily copy and paste verified queries into the BigQuery Conversational Analytics console.\n\n")
        for i, q in enumerate(extracted, 1):
            f.write(f"### Query {i}: {q['question']}\n")
            f.write(f"**Table:** `{q['model']}`\n\n")
            f.write("```sql\n")
            f.write(f"{q['sql']}\n")
            f.write("```\n\n")
            f.write("---\n\n")

    # Write JSON output
    with open(json_output_path, 'w') as f:
        json.dump(extracted, f, indent=2)

    print(f"Extracted {len(extracted)} verified queries.")
    print(f"Markdown output written to {md_output_path}")
    print(f"JSON output written to {json_output_path}")

if __name__ == "__main__":
    main()
