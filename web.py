from flask import Flask, render_template_string, request
import threading
import json
import os
import config

app = Flask(__name__)
SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "norm_hours": 1.0,
        "log_staff": config.LOG_STAFF_CHANNEL,
        "log_punish": config.LOG_PUNISH_CHANNEL,
        "log_list": config.LOG_LIST_CHANNEL
    }

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>VoidPulse Control Panel</title>
    <style>
        body { background-color: #0b0c10; color: #c5c6c7; font-family: sans-serif; padding: 20px; }
        .card { background: #1f2833; padding: 25px; border-radius: 12px; max-width: 600px; margin: 0 auto; }
        h1 { color: #9b59b6; text-align: center; }
        input { width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 6px; border: 1px solid #45a29e; background: #0b0c10; color: #fff; box-sizing: border-box; }
        .btn { background: #9b59b6; color: #fff; border: none; padding: 12px; border-radius: 6px; width: 100%; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🌌 VOIDPULSE PANEL</h1>
        <form action="/api/save" method="POST">
            <label>Суточная норма (часов):</label>
            <input type="number" step="0.5" name="norm_hours" value="{{ settings.norm_hours }}">
            <label>Канал кадрового аудита (ID):</label>
            <input type="text" name="log_staff" value="{{ settings.log_staff }}">
            <label>Канал аудита наказаний (ID):</label>
            <input type="text" name="log_punish" value="{{ settings.log_punish }}">
            <label>Канал списков (ID):</label>
            <input type="text" name="log_list" value="{{ settings.log_list }}">
            <button type="submit" class="btn">💾 Сохранить</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_LAYOUT, settings=load_settings())

@app.route('/api/save', methods=['POST'])
def save_api():
    current = load_settings()
    current['norm_hours'] = float(request.form.get('norm_hours', 1.0))
    current['log_staff'] = int(request.form.get('log_staff', config.LOG_STAFF_CHANNEL))
    current['log_punish'] = int(request.form.get('log_punish', config.LOG_PUNISH_CHANNEL))
    current['log_list'] = int(request.form.get('log_list', config.LOG_LIST_CHANNEL))
    save_settings(current)
    return "<h2 style='color: #57f287; text-align: center;'>✅ Сохранено! <a href='/'>Назад</a></h2>"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
