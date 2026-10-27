from flask import Flask, render_template_string, request, redirect, url_for
import datetime
import os
import threading
import time

app = Flask(__name__)

tickets_list = []
bot_settings = {
    "auto_norm": True,
    "maintenance": False,
    "status_text": "VoidPulse | voidpulse.nexuz.ru"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoidPulse 🌌 | Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: rgba(18, 24, 38, 0.75);
            --primary: #8b5cf6;
            --secondary: #ec4899;
            --accent: #38bdf8;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(139, 92, 246, 0.25);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text); min-height: 100vh; padding: 30px 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 20px; }
        .logo { font-size: 26px; font-weight: 800; background: linear-gradient(135deg, var(--accent), var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 25px; }
        @media(max-width: 768px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 20px; padding: 25px; box-shadow: 0 15px 30px rgba(0,0,0,0.4); }
        .card h2 { font-size: 18px; margin-bottom: 15px; color: var(--text); }
        form { display: flex; flex-direction: column; gap: 12px; }
        input, textarea, select { background: rgba(11, 15, 25, 0.85); border: 1px solid var(--border); border-radius: 10px; padding: 12px; color: var(--text); font-size: 14px; outline: none; }
        button { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { opacity: 0.9; transform: translateY(-2px); }
        .setting-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo">🌌 VOIDPULSE PANEL</div>
            <div style="color: #22c55e; font-size: 14px; font-weight: 600;">● Online (24/7)</div>
        </header>

        <div class="grid">
            <div class="card">
                <h2>⚙️ Управление и Перезагрузка</h2>
                <form action="/reset" method="POST">
                    <button type="submit" style="background: linear-gradient(135deg, #ef4444, #dc2626);">🔄 Перезагрузить систему (Reset)</button>
                </form>
                <form action="/update_settings" method="POST" style="margin-top: 15px;">
                    <div class="setting-row">
                        <span>Авто-проверка нормы (00:00)</span>
                        <input type="checkbox" name="auto_norm" {% if settings.auto_norm %}checked{% endif %}>
                    </div>
                    <label style="font-size: 12px; color: var(--text-muted);">Текст статуса игры:</label>
                    <input type="text" name="status_text" value="{{ settings.status_text }}">
                    <button type="submit">Сохранить настройки 💾</button>
                </form>
            </div>

            <div class="card">
                <h2>🎫 Создать Тикет</h2>
                <form action="/create_ticket" method="POST">
                    <input type="text" name="username" placeholder="Ваш Discord ник" required>
                    <select name="category">
                        <option value="⚙️ Технический вопрос">⚙️ Технический вопрос</option>
                        <option value="🛡️ Жалоба">🛡️ Жалоба</option>
                        <option value="💎 Покупка">💎 Покупка</option>
                    </select>
                    <textarea name="message" placeholder="Суть вопроса..." required></textarea>
                    <button type="submit">Отправить тикет 🚀</button>
                </form>
            </div>
        </div>

        <div class="card" style="margin-top: 25px;">
            <h2>📂 Активные тикеты</h2>
            {% if tickets %}
                {% for t in tickets %}
                <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 8px; margin-top: 8px; font-size: 13px;">
                    <b>{{ t.category }} | {{ t.username }}</b>: {{ t.message }} <span style="float: right; color: var(--text-muted);">{{ t.time }}</span>
                </div>
                {% endfor %}
            {% else %}
                <p style="color: var(--text-muted); font-size: 13px;">Нет активных тикетов.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, tickets=tickets_list, settings=bot_settings)

@app.route('/reset', methods=['POST'])
def reset_bot():
    def delayed_exit():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=delayed_exit).start()
    return "<h2 style='color:white;background:#0b0f19;padding:40px;text-align:center;'>🔄 Система перезагружается... Сервер Render перезапустится через пару секунд.</h2>"

@app.route('/update_settings', methods=['POST'])
def update_settings():
    bot_settings['auto_norm'] = True if request.form.get('auto_norm') else False
    bot_settings['status_text'] = request.form.get('status_text', bot_settings['status_text'])
    return redirect(url_for('home'))

@app.route('/create_ticket', methods=['POST'])
def create_ticket():
    username = request.form.get('username')
    category = request.form.get('category')
    message = request.form.get('message')
    if username and message:
        tickets_list.insert(0, {
            'username': username, 'category': category,
            'message': message, 'time': datetime.datetime.now().strftime('%H:%M')
        })
    return redirect(url_for('home'))

def keep_alive():
    def run():
        app.run(host='0.0.0.0', port=10000)
    threading.Thread(target=run).start()
