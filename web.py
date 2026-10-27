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
ai_logs = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoidPulse 🌌 | LuckPerms Style Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --sidebar-bg: #111827;
            --card-bg: rgba(18, 24, 38, 0.85);
            --primary: #8b5cf6;
            --secondary: #ec4899;
            --accent: #38bdf8;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(139, 92, 246, 0.2);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text); display: flex; min-height: 100vh; }
        
        sidebar { width: 260px; background: var(--sidebar-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 20px; transition: 0.3s; }
        .logo { font-size: 22px; font-weight: 800; background: linear-gradient(135deg, var(--accent), var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 30px; display: flex; align-items: center; gap: 10px; }
        .nav-item { padding: 12px 16px; border-radius: 10px; color: var(--text-muted); text-decoration: none; font-weight: 600; margin-bottom: 6px; transition: 0.2s; display: flex; align-items: center; gap: 10px; cursor: pointer; }
        .nav-item:hover, .nav-item.active { background: rgba(139, 92, 246, 0.15); color: var(--text); border-left: 4px solid var(--primary); }

        .main-content { flex: 1; padding: 30px; overflow-y: auto; max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        .menu-toggle { font-size: 22px; cursor: pointer; display: none; background: none; border: none; color: var(--text); }

        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media(max-width: 900px) { .grid { grid-template-columns: 1fr; } sidebar { position: absolute; left: -260px; height: 100%; z-index: 100; } sidebar.open { left: 0; } .menu-toggle { display: block; } }

        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px; }
        .card h2 { font-size: 18px; margin-bottom: 15px; color: var(--text); display: flex; align-items: center; gap: 8px; }
        
        form { display: flex; flex-direction: column; gap: 12px; }
        input, textarea, select { background: rgba(11, 15, 25, 0.9); border: 1px solid var(--border); border-radius: 10px; padding: 12px; color: var(--text); font-size: 14px; outline: none; }
        input:focus, textarea:focus { border-color: var(--primary); }
        button { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        button:hover { opacity: 0.9; transform: translateY(-2px); }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .setting-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }
    </style>
</head>
<body>

    <sidebar id="sidebar">
        <div class="logo">🌌 VoidPulse</div>
        <a class="nav-item active" onclick="switchTab('dashboard', this)">📊 Дашборд</a>
        <a class="nav-item" onclick="switchTab('roles', this)">👑 Роли и Права</a>
        <a class="nav-item" onclick="switchTab('texts', this)">💬 Тексты и Сообщения</a>
        <a class="nav-item" onclick="switchTab('files', this)">📁 Конфиги и Файлы</a>
        <a class="nav-item" onclick="switchTab('ai', this)">🤖 ИИ-Ассистент задача</a>
        <a class="nav-item" onclick="switchTab('tickets', this)">🎫 Тикеты</a>
    </sidebar>

    <div class="main-content">
        <header>
            <div style="display: flex; align-items: center; gap: 15px;">
                <button class="menu-toggle" onclick="toggleMenu()">☰</button>
                <h1 style="font-size: 20px;">Панель управления проектом</h1>
            </div>
            <div style="color: #22c55e; font-size: 13px; font-weight: 600;">● Online (24/7)</div>
        </header>

        <div id="dashboard" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h2>⚙️ Управление Системой</h2>
                    <form action="/reset" method="POST">
                        <button type="submit" style="background: linear-gradient(135deg, #ef4444, #dc2626);">🔄 Перезагрузить систему (Reset)</button>
                    </form>
                    <form action="/update_settings" method="POST" style="margin-top: 15px;">
                        <div class="setting-row">
                            <span>Авто-проверка нормы (00:00)</span>
                            <input type="checkbox" name="auto_norm" {% if settings.auto_norm %}checked{% endif %}>
                        </div>
                        <label style="font-size: 12px; color: var(--text-muted);">Статус игры бота:</label>
                        <input type="text" name="status_text" value="{{ settings.status_text }}">
                        <button type="submit">Сохранить настройки 💾</button>
                    </form>
                </div>
                <div class="card">
                    <h2>📈 Статус Хостинга</h2>
                    <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 10px;">Платформа: <b>Render Cloud</b></p>
                    <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 10px;">Связь с таблицей: <b>Google Sheets Sync</b></p>
                    <p style="color: var(--text-muted); font-size: 14px;">IP сервера: <b style="color:var(--accent)">voidpulse.nexuz.ru</b></p>
                </div>
            </div>
        </div>

        <div id="roles" class="tab-content">
            <div class="card">
                <h2>👑 Настройка 8 Ролей состава</h2>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 15px;">Синхронизировано с Google Таблицей персонала.</p>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div class="setting-row"><span>1. Владелец проекта</span><b style="color:var(--accent)">Full Access</b></div>
                    <div class="setting-row"><span>2. Со-Владелец</span><b style="color:var(--accent)">Admin</b></div>
                    <div class="setting-row"><span>3. Куратор</span><b style="color:var(--accent)">Moderator</b></div>
                    <div class="setting-row"><span>4. Ст.Администратор</span><b style="color:var(--accent)">Staff</b></div>
                    <div class="setting-row"><span>5. Администратор</span><b style="color:var(--accent)">Staff</b></div>
                    <div class="setting-row"><span>6. Ст.Модератор</span><b style="color:var(--accent)">Staff</b></div>
                    <div class="setting-row"><span>7. Модератор</span><b style="color:var(--accent)">Staff</b></div>
                    <div class="setting-row"><span>8. Хелпер</span><b style="color:var(--accent)">Helper</b></div>
                </div>
            </div>
        </div>

        <div id="texts" class="tab-content">
            <div class="card">
                <h2>💬 Тексты и Шаблоны Сообщений</h2>
                <form action="/save_text" method="POST">
                    <label style="font-size: 12px; color: var(--text-muted);">Текст ежедневного отчета нормы в ЛС:</label>
                    <textarea name="norm_text">📊 Ежедневный отчёт по норме персонала. Напоминание: наступило 00:00 МСК. Проверьте активность!</textarea>
                    <button type="submit" style="margin-top: 10px;">Сохранить текст 💾</button>
                </form>
            </div>
        </div>

        <div id="files" class="tab-content">
            <div class="card">
                <h2>📁 Редактор Конфигов</h2>
                <label style="font-size: 12px; color: var(--text-muted);">config.py / Токены:</label>
                <textarea style="height: 120px; font-family: monospace;">TOKEN = "Protected"
SPREADSHEET_ID = "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves"</textarea>
                <button style="margin-top: 10px;" onclick="alert('Сохранено в кэш панели!')">Сохранить файл 💾</button>
            </div>
        </div>

        <div id="ai" class="tab-content">
            <div class="card">
                <h2>🤖 ИИ-Ассистент (Поставить задачу)</h2>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 15px;">Напиши задачу для ИИ, и система зафиксирует её для выполнения кода.</p>
                <form action="/ai_task" method="POST">
                    <textarea name="task" placeholder="Например: Добавь новую команду /online или измени цвет эмбедов..." required></textarea>
                    <button type="submit">Отправить задачу ИИ ⚡</button>
                </form>
                {% if ai_logs %}
                <div style="margin-top: 20px; background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px;">
                    <b style="font-size: 13px; color: var(--accent);">История задач:</b>
                    {% for log in ai_logs %}
                    <p style="font-size: 13px; color: var(--text-muted); margin-top: 5px;">• {{ log }}</p>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>

        <div id="tickets" class="tab-content">
            <div class="card">
                <h2>🎫 Активные тикеты с сайта</h2>
                {% if tickets %}
                    {% for t in tickets %}
                    <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; margin-top: 10px; font-size: 13px;">
                        <b>{{ t.category }} | {{ t.username }}</b>: {{ t.message }} <span style="float: right; color: var(--text-muted);">{{ t.time }}</span>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: var(--text-muted); font-size: 13px;">Нет активных тикетов.</p>
                {% endif %}
            </div>
        </div>

    </div>

    <script>
        function switchTab(tabId, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            element.classList.add('active');
            if(window.innerWidth <= 900) { document.getElementById('sidebar').classList.remove('open'); }
        }
        function toggleMenu() { document.getElementById('sidebar').classList.toggle('open'); }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, tickets=tickets_list, settings=bot_settings, ai_logs=ai_logs)

@app.route('/reset', methods=['POST'])
def reset_bot():
    def delayed_exit():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=delayed_exit).start()
    return """
    <body style='background:#0b0f19;color:white;font-family:sans-serif;text-align:center;padding-top:100px;'>
        <h2>🔄 Система перезагружается...</h2>
        <p>Сервер перезапускается. Страница обновится автоматически через 12 секунд.</p>
        <script>
            setTimeout(() => {
                window.location.href = "/";
            }, 12000);
        </script>
    </body>
    """

@app.route('/update_settings', methods=['POST'])
def update_settings():
    bot_settings['auto_norm'] = True if request.form.get('auto_norm') else False
    bot_settings['status_text'] = request.form.get('status_text', bot_settings['status_text'])
    return redirect(url_for('home'))

@app.route('/ai_task', methods=['POST'])
def ai_task():
    task = request.form.get('task')
    if task:
        ai_logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M')}] {task}")
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
