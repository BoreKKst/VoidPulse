from flask import Flask, render_template_string, request, redirect, session
import datetime
import os
import threading
import time
import logging
import config

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.secret_key = "voidpulse_lp_editor_secret"

bot_settings = {
    "auto_norm": True,
    "status_text": "VoidPulse | voidpulse.nexuz.ru",
    "norm_text": "📊 Отчёт по норме. 00:00 МСК."
}
custom_commands = []
ai_logs = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoidPulse | Secret Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --bg-color: #0b0f19; --sidebar-bg: #111827; --card-bg: rgba(18, 24, 38, 0.9); --primary: #8b5cf6; --text: #f8fafc; --text-muted: #94a3b8; --border: rgba(139, 92, 246, 0.25); }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text); display: flex; min-height: 100vh; }
        sidebar { width: 260px; background: var(--sidebar-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 20px; }
        .logo { font-size: 20px; font-weight: 800; color: var(--primary); margin-bottom: 25px; }
        .nav-item { padding: 12px 16px; border-radius: 10px; color: var(--text-muted); text-decoration: none; font-weight: 600; margin-bottom: 6px; cursor: pointer; }
        .nav-item.active { background: rgba(139, 92, 246, 0.15); color: var(--text); border-left: 4px solid var(--primary); }
        .main-content { flex: 1; padding: 30px; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 25px; margin-bottom: 20px; }
        input, textarea { width: 100%; background: #0b0f19; border: 1px solid var(--border); border-radius: 8px; padding: 12px; color: #fff; margin-bottom: 10px; outline: none; }
        button { background: var(--primary); color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <sidebar>
        <div class="logo">🌌 LP Secret Panel</div>
        <a class="nav-item active" onclick="switchTab('dash', this)">⚙️ Дашборд</a>
        <a class="nav-item" onclick="switchTab('cmds', this)">⚡ Команды</a>
    </sidebar>
    <div class="main-content">
        <div id="dash" class="tab-content active">
            <div class="card">
                <h2>Управление и Рестарт</h2>
                <p style="color:var(--text-muted); margin-bottom: 15px;">После сохранения параметров бот автоматически применит настройки и уведомит в ЛС.</p>
                <form action="/save_and_restart" method="POST">
                    <label>Статус бота:</label>
                    <input type="text" name="status" value="{{ settings.status_text }}">
                    <label>Текст отчета (00:00):</label>
                    <textarea name="norm_text">{{ settings.norm_text }}</textarea>
                    <button type="submit" style="background:#ef4444;">💾 Сохранить и Перезапустить (Reset)</button>
                </form>
            </div>
        </div>
        <div id="cmds" class="tab-content">
            <div class="card">
                <h2>Кастомные ответы (В памяти)</h2>
                <form action="/add_cmd" method="POST">
                    <input type="text" name="cmd" placeholder="Команда (напр. rules)" required>
                    <textarea name="resp" placeholder="Ответ..." required></textarea>
                    <button type="submit">Добавить</button>
                </form>
                {% for c in cmds %}
                    <p style="margin-top:10px;"><b>/{{ c.name }}</b> — {{ c.response }} <a href="/del_cmd/{{ c.name }}" style="color:#ef4444;">[Удалить]</a></p>
                {% endfor %}
            </div>
        </div>
    </div>
    <script>
        function switchTab(id, el) {
            document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(e => e.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            el.classList.add('active');
        }
    </script>
</body>
</html>
"""

@app.before_request
def require_token():
    if request.path.startswith('/static'): return
    # Проверка секретного токена в ссылке
    if request.args.get('token') == config.WEB_SECRET_TOKEN:
        session['auth'] = True
    if not session.get('auth'):
        return "<body style='background:#0b0f19;color:#ef4444;text-align:center;padding-top:100px;font-family:sans-serif;'><h2>⛔ ДОСТУП ЗАПРЕЩЁН</h2><p>Используйте защищенную ссылку из команды /web в Discord.</p></body>", 403

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, settings=bot_settings, cmds=custom_commands)

@app.route('/save_and_restart', methods=['POST'])
def save_and_restart():
    bot_settings['status_text'] = request.form.get('status', bot_settings['status_text'])
    bot_settings['norm_text'] = request.form.get('norm_text', bot_settings['norm_text'])
    
    # Создаем файл-метку, чтобы после рестарта main.py написал в ЛС
    with open("restart_queue.txt", "w") as f:
        f.write("restarting")
        
    threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
    return "<body style='background:#0b0f19;color:#22c55e;text-align:center;padding-top:100px;font-family:sans-serif;'><h2>🔄 Перезагрузка Render...</h2><p>Ожидайте уведомления в ЛС Discord.</p><script>setTimeout(()=>window.location.href='/?token=" + config.WEB_SECRET_TOKEN + "', 15000);</script></body>"

@app.route('/add_cmd', methods=['POST'])
def add_cmd():
    n, r = request.form.get('cmd'), request.form.get('resp')
    if n and r: custom_commands.append({"name": n.strip().lstrip('/'), "response": r})
    return redirect(url_for('home'))

@app.route('/del_cmd/<name>')
def del_cmd(name):
    global custom_commands
    custom_commands = [c for c in custom_commands if c['name'] != name]
    return redirect(url_for('home'))

def keep_alive():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
