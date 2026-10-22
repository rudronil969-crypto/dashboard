
import subprocess, json, os, datetime
os.environ["NOTION_API_KEY"] = "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"

# Fetch Notion DB
cmd = [
    "curl", "-s", "-X", "POST",
    "https://api.notion.com/v1/databases/40075580-e0b1-803d-ab31-ca7ce1ff5af7/query",
    "-H", "Authorization: Bearer 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",
    "-H", "Notion-Version: 2022-06-28",
    "-H", "Content-Type: application/json",
    "-d", '{"page_size":100}'
]
res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
data = json.loads(res.stdout)
results = data.get("results", [])

cards = []
for r in results:
    props = r.get("properties", {})
    name_prop = props.get("Name", {})
    title_text = name_prop.get("title", [{}])[0].get("text", {}).get("content", "Unknown") if isinstance(name_prop.get("title"), list) else "Unknown"
    # Extract body info from children or content
    cards.append(title_text)

print("Synced leads from Notion:", cards)
# Note: Full HTML regeneration could be done here; for now we verify sync works
