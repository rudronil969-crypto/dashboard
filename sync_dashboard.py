
import subprocess, json, os, datetime
# Secure token load: prefer env variable, then credentials.json
NOTION_KEY = os.environ.get("NOTION_API_KEY", "")
if not NOTION_KEY and os.path.exists("/opt/data/credentials.json"):
    try:
        with open("/opt/data/credentials.json") as f:
            import json
            data = json.load(f)
            # Note: service account file does not contain Notion token by default.
            # If credentials.json is a service account (no Notion token), skip.
            # For Notion-only tasks, use .env file or direct env injection by user.
            pass
    except:
        pass
# Try reading .env for NOTION_API_KEY
if not NOTION_KEY:
    if os.path.exists("/opt/data/.env"):
        with open("/opt/data/.env") as f:
            for line in f:
                if line.startswith("NOTION_API_KEY="):
                    NOTION_KEY = line.split("=", 1)[1].strip()
# Fallback: check environment only (no hardcoded token)
if not NOTION_KEY:
    NOTION_KEY = os.environ.get("NOTION_API_TOKEN", "")

os.environ["NOTION_API_KEY"] = NOTION_KEY
os.environ["NOTION_KEYRING"] = "0"

cmd = [
    "curl", "-s", "-X", "POST",
    "https://api.notion.com/v1/databases/40075580-e0b1-803d-ab31-ca7ce1ff5af7/query",
    "-H", f"Authorization: Bearer {NOTION_KEY}",
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
    cards.append(title_text)
print("Synced leads from Notion:", cards)
