from flask import Flask, render_template_string, request, redirect, url_for, session
import datetime
import os
import threading
import time

app = Flask(__name__)
app.secret_key = "voidpulse_lp_editor_secret"

tickets_list = []
ai_logs = []
custom_commands = [
    {"name": "online", "response": "Проверка через /list"},
    {"name": "rules", "response": "Правила сервера VoidPulse: уважение и адекватность."}
]

allowed_users = {
    "BoreKKst": "admin2026"
}

bot_settings = {
    "auto_norm": True,
    "status_text": "VoidPulse | voidpulse.nexuz.ru",
    "norm_text": "📊 Ежедневный отчёт по норме персонала. Напоминание: наступило 00:00 МСК. Проверьте активность!"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoidPulse 🌌 | LP Editor</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --sidebar-bg: #111827;
            --card-bg: rgba(18, 24, 38, 0.9);
            --primary: #8b5cf6;
            --secondary: #ec4899;
            --accent: #38bdf8;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(139, 92, 246, 0.25);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-color); color: var(--text); display: flex; min-height: 100vh; }
        
        sidebar { width: 260px; background: var(--sidebar-bg); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 20px; }
        .logo { font-size: 20px; font-weight: 800; background: linear-gradient(135deg, var(--accent), var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 25px; display: flex; align-items: center; gap: 10px; }
        .nav-item { padding: 12px 16px; border-radius: 10px; color: var(--text-muted); text-decoration: none; font-weight: 600; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; cursor: pointer; transition: 0.2s; }
        .nav-item:hover, .nav-item.active { background: rgba(139, 92, 246, 0.15); color: var(--text); border-left: 4px solid var(--primary); }

        .main-content { flex: 1; padding: 30px; overflow-y: auto; max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }

        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media(max-width: 900px) { .grid { grid-template-columns: 1fr; } sidebar { position: absolute; left: -260px; height: 100%; z-index: 100; } }

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
        <div class="logo">🌌 LP Editor</div>
        <a class="nav-item active" onclick="switchTab('dashboard', this)">📊 Дашборд</a>
        <a class="nav-item" onclick="switchTab('roles', this)">👑 Роли и Права</a>
        <a class="nav-item" onclick="switchTab('texts', this)">💬 Тексты и Шаблоны</a>
        <a class="nav-item" onclick="switchTab('commands', this)">⚡ Команды бота</a>
        <a class="nav-item" onclick="switchTab('files', this)">📁 Конфиги</a>
        <a class="nav-item" onclick="switchTab('ai', this)">🤖 ИИ-Задачи</a>
        <a class="nav-item" onclick="switchTab('tickets', this)">🎫 Тикеты</a>
        <a class="nav-item" onclick="switchTab('access', this)">👥 Доступы</a>
        <a class="nav-item" href="/logout" style="color: #ef4444; margin-top: auto;">🚪 Выйти</a>
    </sidebar>

    <div class="main-content">
        <header>
            <h1 style="font-size: 20px;">Редактор проекта ({{ session.user }})</h1>
            <div style="color: #22c55e; font-size: 13px; font-weight: 600;">● Online (24/7)</div>
        </header>

        <!-- DASHBOARD -->
        <div id="dashboard" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h2>⚙️ Управление системой</h2>
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
                        <button type="submit">Сохранить 💾</button>
                    </form>
                </div>
                <div class="card">
                    <h2>📈 Информация</h2>
                    <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 10px;">Хостинг: <b>Render Cloud</b></p>
                    <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 10px;">База данных: <b>Google Sheets</b></p>
                    <p style="color: var(--text-muted); font-size: 14px;">Сервер: <b style="color:var(--accent)">voidpulse.nexuz.ru</b></p>
                </div>
            </div>
        </div>

        <!-- ROLES -->
        <div id="roles" class="tab-content">
            <div class="card">
                <h2>👑 8 Основных Ролей Проекта</h2>
                <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 10px;">
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

        <!-- TEXTS -->
        <div id="texts" class="tab-content">
            <div class="card">
                <h2>💬 Тексты и Уведомления</h2>
                <form action="/update_texts" method="POST">
                    <label style="font-size: 12px; color: var(--text-muted);">Текст отчета нормы в ЛС (00:00):</label>
                    <textarea name="norm_text" style="height: 100px;">{{ settings.norm_text }}</textarea>
                    <button type="submit" style="margin-top: 10px;">Сохранить текст 💾</button>
                </form>
            </div>
        </div>

        <!-- COMMANDS -->
        <div id="commands" class="tab-content">
            <div class="card">
                <h2>⚡ Кастомные команды</h2>
                <form action="/add_command" method="POST" style="margin-bottom: 20px;">
                    <input type="text" name="cmd_name" placeholder="Имя команды (например: info)" required>
                    <textarea name="cmd_response" placeholder="Текст ответа..." required></textarea>
                    <button type="submit">Добавить команду ➕</button>
                </form>
                {% for c in custom_commands %}
                <div class="setting-row">
                    <span><b>/{{ c.name }}</b> — {{ c.response }}</span>
                    <a href="/delete_command/{{ c.name }}" style="color: #ef4444; text-decoration: none;">Удалить 🗑️</a>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- FILES -->
        <div id="files" class="tab-content">
            <div class="card">
                <h2>📁 Конфигурационные файлы</h2>
                <label style="font-size: 12px; color: var(--text-muted);">config.py settings:</label>
                <textarea style="height: 120px; font-family: monospace;">TOKEN = "Protected"
SPREADSHEET_ID = "1gAAyXJ20cAKBHCUzAl9H-v8DLm4aEaUMpwt2VLbuves"</textarea>
                <button style="margin-top: 10px;" onclick="alert('Сохранено!')">Сохранить файл 💾</button>
            </div>
        </div>

        <!-- AI TASKS -->
        <div id="ai" class="tab-content">
            <div class="card">
                <h2>🤖 ИИ-Задачи</h2>
                <form action="/ai_task" method="POST">
                    <textarea name="task" placeholder="Напишите задачу для ИИ..." required></textarea>
                    <button type="submit">Отправить задачу ⚡</button>
                </form>
                {% if ai_logs %}
                <div style="margin-top: 20px; background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px;">
                    {% for log in ai_logs %}
                    <p style="font-size: 13px; color: var(--text-muted);">• {{ log }}</p>
                    {% endfor %}
                </div>
                {% endif %}
            </div>
        </div>

        <!-- TICKETS -->
        <div id="tickets" class="tab-content">
            <div class="card">
                <h2>🎫 Тикеты поддержки</h2>
                {% if tickets %}
                    {% for t in tickets %}
                    <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; margin-top: 10px; font-size: 13px;">
                        <b>{{ t.category }} | {{ t.username }}</b>: {{ t.message }}
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: var(--text-muted); font-size: 13px;">Нет активных тикетов.</p>
                {% endif %}
            </div>
        </div>

        <!-- ACCESS -->
        <div id="access" class="tab-content">
            <div class="card">
                <h2>👥 Доступы к панели (LP style)</h2>
                <form action="/add_user" method="POST" style="margin-bottom: 20px;">
                    <input type="text" name="new_user" placeholder="Логин" required>
                    <input type="password" name="new_pass" placeholder="Пароль" required>
                    <button type="submit">Добавить пользователя ➕</button>
                </form>
                {% for usr in users_list %}
                <div class="setting-row">
                    <span>👤 <b>{{ usr }}</b></span>
                    {% if usr != "BoreKKst" %}
                    <a href="/delete_user/{{ usr }}" style="color: #ef4444; text-decoration: none;">Удалить 🗑️</a>
                    {% else %}
                    <span style="font-size: 12px; color: var(--text-muted);">Главный владелец</span>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>

    </div>

    <script>
        function switchTab(tabId, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            element.classList.add('active');
        }
    </script>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>VoidPulse 🌌 | LP Editor Login</title>
    <style>
        body { background: #0b0f19; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .card { background: #111827; padding: 40px; border-radius: 16px; border: 1px solid rgba(139,92,246,0.3); width: 350px; }
        input { width: 100%; padding: 12px; margin-bottom: 15px; background: #0b0f19; border: 1px solid #38bdf8; color: #fff; border-radius: 8px; outline: none; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #8b5cf6, #ec4899); border: none; color: #fff; font-weight: bold; border-radius: 8px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="text-align:center; margin-bottom:20px;">🌌 LP Editor Login</h2>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="Логин" required>
            <input type="password" name="password" placeholder="Пароль" required>
            <button type="submit">Войти</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') in allowed_users and allowed_users[request.form.get('username')] == request.form.get('password'):
            session['user'] = request.form.get('username')
            return redirect(url_for('home'))
        return render_template_string(LOGIN_TEMPLATE)
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE, tickets=tickets_list, settings=bot_settings, ai_logs=ai_logs, custom_commands=custom_commands, users_list=allowed_users.keys())

@app.route('/reset', methods=['POST'])
def reset_bot():
    if 'user' not in session: return redirect(url_for('login'))
    threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
    return "<body style='background:#0b0f19;color:white;text-align:center;padding-top:100px;'><h2>🔄 Перезагрузка...</h2><script>setTimeout(() => window.location.href='/', 12000);</script></body>"

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user' not in session: return redirect(url_for('login'))
    bot_settings['auto_norm'] = True if request.form.get('auto_norm') else False
    bot_settings['status_text'] = request.form.get('status_text', bot_settings['status_text'])
    return redirect(url_for('home'))

@app.route('/update_texts', methods=['POST'])
def update_texts():
    if 'user' not in session: return redirect(url_for('login'))
    bot_settings['norm_text'] = request.form.get('norm_text', bot_settings['norm_text'])
    return redirect(url_for('home'))

@app.route('/add_command', methods=['POST'])
def add_command():
    if 'user' not in session: return redirect(url_for('login'))
    global custom_commands
    name, resp = request.form.get('cmd_name').strip().lstrip('/'), request.form.get('cmd_response')
    if name and resp:
        custom_commands = [c for c in custom_commands if c['name'] != name]
        custom_commands.append({"name": name, "response": resp})
    return redirect(url_for('home'))

@app.route('/delete_command/<name>')
def delete_command(name):
    if 'user' not in session: return redirect(url_for('login'))
    global custom_commands
    custom_commands = [c for c in custom_commands if c['name'] != name]
    return redirect(url_for('home'))

@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user' not in session: return redirect(url_for('login'))
    if request.form.get('new_user') and request.form.get('new_pass'):
        allowed_users[request.form.get('new_user').strip()] = request.form.get('new_pass').strip()
    return redirect(url_for('home'))

@app.route('/delete_user/<usr>')
def delete_user(usr):
    if 'user' not in session or usr == "BoreKKst": return redirect(url_for('login'))
    if usr in allowed_users: del allowed_users[usr]
    return redirect(url_for('home'))

@app.route('/ai_task', methods=['POST'])
def ai_task():
    if 'user' not in session: return redirect(url_for('login'))
    if request.form.get('task'): ai_logs.insert(0, f"[{datetime.datetime.now().strftime('%H:%M')}] {request.form.get('task')}")
    return redirect(url_for('home'))

@app.route('/create_ticket', methods=['POST'])
def create_ticket():
    if request.form.get('username') and request.form.get('message'):
        tickets_list.insert(0, {'username': request.form.get('username'), 'category': request.form.get('category'), 'message': request.form.get('message'), 'time': datetime.datetime.now().strftime('%H:%M')})
    return redirect(url_for('home'))

def keep_alive():
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
