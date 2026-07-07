import argparse

from google.cloud import geminidataanalytics_v1alpha

import agent_config

parser = argparse.ArgumentParser(description="Send one question to the NBA data agent.")
agent_config.add_target_arg(parser)
parser.add_argument("--question", default="Who is the tallest player?",
                    help="Question to send (default is an out-of-scope trap)")
args = parser.parse_args()
cfg = agent_config.resolve(args.target)
print(f"TARGET: {cfg['target'].upper()}  agent={cfg['agent_id']}  dataset={cfg['dataset']}")

client = geminidataanalytics_v1alpha.DataChatServiceClient(
    client_options={"api_endpoint": "geminidataanalytics.us.rep.googleapis.com"}
)

parent = f"projects/{agent_config.PROJECT_ID}/locations/{agent_config.LOCATION}"

msg = geminidataanalytics_v1alpha.Message(
    user_message=geminidataanalytics_v1alpha.UserMessage(
        text=args.question
    )
)

request = geminidataanalytics_v1alpha.ChatRequest(
    parent=parent,
    messages=[msg],
    data_agent_context=geminidataanalytics_v1alpha.DataAgentContext(
        data_agent=cfg["agent_name"]
    )
)
try:
    for chunk in client.chat(request=request):
        print(chunk)
except Exception as e:
    print("Error:", e)
