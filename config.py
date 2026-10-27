import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves")
OWNER_ID = int(os.getenv("OWNER_ID", "1374053953301385308"))
WEB_SECRET_TOKEN = os.getenv("WEB_SECRET_TOKEN", "super_admin_voidpulse_777")

google_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
if google_json and not os.path.exists("credentials.json"):
    try:
        with open("credentials.json", "w", encoding="utf-8") as f:
            f.write(google_json)
    except Exception as e:
        print(f"⚠️ Ошибка создания credentials.json: {e}")
