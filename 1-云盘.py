from flask import Flask, request, session, redirect, url_for, render_template_string, send_from_directory
import os, time, sqlite3, shutil
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'uploads'
PUBLIC_FOLDER = os.path.join(UPLOAD_FOLDER, 'public')
DATABASE = 'cloud.db'

os.makedirs(PUBLIC_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

# 初始化数据库
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password TEXT,
                        ip TEXT
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS file_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT,
                        receiver TEXT,
                        filename TEXT,
                        status TEXT
                    )''')
        conn.commit()

init_db()

# 工具函数
def db_query(query, args=(), one=False):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        conn.commit()
        return (rv[0] if rv else None) if one else rv

def write_log(action, filename, username='public'):
    time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ip = request.remote_addr
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(f'[{time_now}] IP:{ip} 用户:{username} {action}: {filename}\n')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    ip = request.remote_addr
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if db_query('SELECT * FROM users WHERE username = ?', [username], one=True):
            error = '用户名已存在'
        else:
            db_query('INSERT INTO users (username, password, ip) VALUES (?, ?, ?)', [username, password, ip])
            os.makedirs(os.path.join(UPLOAD_FOLDER, username), exist_ok=True)
            return redirect(url_for('login'))
    return render_template_string(template_base('注册个人云盘', '''
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="post" class="my-3">
            <input class="form-control my-2" name="username" placeholder="用户名" required>
            <input class="form-control my-2" type="password" name="password" placeholder="密码" required>
            <button class="btn btn-primary">注册</button>
        </form>
    '''), error=error)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = db_query('SELECT * FROM users WHERE username=? AND password=?', [username, password], one=True)
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin_dashboard') if username == 'admin' else url_for('user_upload'))
        error = '用户名或密码错误'
    return render_template_string(template_base('登录', '''
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="post" class="my-3">
            <input class="form-control my-2" name="username" placeholder="用户名" required>
            <input class="form-control my-2" type="password" name="password" placeholder="密码" required>
            <button class="btn btn-primary">登录</button>
        </form>
        <a href="/register" class="btn btn-link">注册</a>
        <a href="/upload_public" class="btn btn-link">公共云盘</a>
    '''), error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if session['username'] != 'admin':
        return '无权限访问'
    logs = open('log.txt', encoding='utf-8').read()
    users = db_query('SELECT username FROM users')
    files_html = ''
    for u in users:
        user_path = os.path.join(UPLOAD_FOLDER, u[0])
        if os.path.exists(user_path):
            files = os.listdir(user_path)
            files_html += f'<h5>{u[0]}</h5><ul>' + ''.join(f'<li>{f}</li>' for f in files) + '</ul>'
    return render_template_string(template_base('管理员面板', '''
        <h3>日志</h3><pre>{{ logs }}</pre>
        <h3>所有用户文件</h3>{{ files|safe }}
        <a href="/logout" class="btn btn-secondary">退出</a>
    '''), logs=logs, files=files_html)

@app.route('/user_upload', methods=['GET', 'POST'])
@login_required
def user_upload():
    username = session['username']
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    if request.method == 'POST':
        for file in request.files.getlist('files'):
            if file:
                file.save(os.path.join(user_folder, file.filename))
                write_log('上传', file.filename, username)
        return redirect(url_for('user_files'))
    return render_template_string(template_base('上传文件（个人云盘）', '''
        <form method="post" enctype="multipart/form-data">
            <input class="form-control my-2" type="file" name="files" multiple>
            <button class="btn btn-success">上传</button>
        </form>
        <a href="/user_files" class="btn btn-link">我的文件</a>
        <a href="/file_requests" class="btn btn-link">文件请求</a>
        <a href="/change_password" class="btn btn-warning">修改密码</a>
        <a href="/delete_account" class="btn btn-danger">删除账号</a>
        <a href="/logout" class="btn btn-secondary">退出登录</a>
    '''))

@app.route('/user_files')
@login_required
def user_files():
    username = session['username']
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    files = os.listdir(user_folder)

    file_list = ''
    for f in files:
        file_list += f'''
        <li>
            {f}
            <a href="/download_user/{f}" class="btn btn-sm btn-primary">下载</a>
            <button class="btn btn-sm btn-warning" onclick="sendFilePrompt('{f}')">发送</button>
            <a href="/delete_file/{f}" class="btn btn-sm btn-danger" onclick="return confirm('确定要删除 {f} 吗？')">删除</a>
        </li>'''

    return render_template_string(template_base('我的文件', f'''
        <ul>{file_list}</ul>
        <a class="btn btn-link" href="/user_upload">返回上传</a>
        <script>
            function sendFilePrompt(filename) {{
                const recipient = prompt("请输入接收者用户名：");
                if (recipient) {{
                    fetch("/send_file", {{
                        method: "POST",
                        headers: {{
                            "Content-Type": "application/x-www-form-urlencoded"
                        }},
                        body: "filename=" + encodeURIComponent(filename) + "&recipient=" + encodeURIComponent(recipient)
                    }}).then(r => r.text()).then(alert);
                }}
            }}
        </script>
    '''))

@app.route('/delete_file/<filename>')
@login_required
def delete_file(filename):
    username = session['username']
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    file_path = os.path.join(user_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        write_log('删除', filename, username)
        return redirect(url_for('user_files'))
    else:
        return '文件不存在'


@app.route('/send_file', methods=['POST'])
@login_required
def send_file():
    sender = session['username']
    recipient = request.form.get('recipient')
    filename = request.form.get('filename')

    # 确保接收用户存在
    if not db_query('SELECT * FROM users WHERE username=?', [recipient], one=True):
        return '接收用户不存在'

    sender_folder = os.path.join(UPLOAD_FOLDER, sender)
    recipient_folder = os.path.join(UPLOAD_FOLDER, recipient)
    os.makedirs(recipient_folder, exist_ok=True)

    src_path = os.path.join(sender_folder, filename)
    dst_path = os.path.join(recipient_folder, filename)

    if not os.path.exists(src_path):
        return '原文件不存在'

    if os.path.exists(dst_path):
        return '对方已有同名文件'

    import shutil
    shutil.copy2(src_path, dst_path)
    write_log('发送', filename, username=sender)
    return '发送成功'


@app.route('/file_requests')
@login_required
def file_requests():
    username = session['username']
    rows = db_query('SELECT id, sender, filename FROM file_requests WHERE receiver=? AND status="pending"', [username])
    html = ''.join(f'<li>{r[1]} 想发送文件 {r[2]} '
                   f'<a class="btn btn-sm btn-success" href="/accept_request/{r[0]}">接受</a> '
                   f'<a class="btn btn-sm btn-danger" href="/reject_request/{r[0]}">拒绝</a></li>' for r in rows)
    return render_template_string(template_base('文件请求', f'<ul>{html}</ul><a href="/user_upload">返回</a>'))

@app.route('/accept_request/<int:req_id>')
@login_required
def accept_request(req_id):
    req = db_query('SELECT sender, receiver, filename FROM file_requests WHERE id=?', [req_id], one=True)
    if req:
        src = os.path.join(UPLOAD_FOLDER, req[0], req[2])
        dst = os.path.join(UPLOAD_FOLDER, req[1], req[2])
        if os.path.exists(src):
            shutil.copy2(src, dst)
            db_query('UPDATE file_requests SET status="accepted" WHERE id=?', [req_id])
            write_log('接受文件', req[2], req[1])
    return redirect(url_for('file_requests'))

@app.route('/reject_request/<int:req_id>')
@login_required
def reject_request(req_id):
    db_query('UPDATE file_requests SET status="rejected" WHERE id=?', [req_id])
    return redirect(url_for('file_requests'))

@app.route('/download_user/<filename>')
@login_required
def download_user(filename):
    username = session['username']
    folder = os.path.join(UPLOAD_FOLDER, username)
    write_log('下载', filename, username)
    return send_from_directory(folder, filename, as_attachment=True)

@app.route('/upload_public', methods=['GET', 'POST'])
def upload_public():
    msg = None
    if request.method == 'POST':
        for f in request.files.getlist('files'):
            if f:
                f.save(os.path.join(PUBLIC_FOLDER, f.filename))
                write_log('公共上传', f.filename)
        msg = '上传成功'
    return render_template_string(template_base('上传公共文件', '''
        {% if message %}<div class="alert alert-info">{{ message }}</div>{% endif %}
        <form method="post" enctype="multipart/form-data">
            <input class="form-control my-2" type="file" name="files" multiple>
            <button class="btn btn-success">上传</button>
        </form>
        <a href="/files_public" class="btn btn-link">查看公共文件</a>
    '''), message=msg)

@app.route('/files_public')
def files_public():
    files = os.listdir(PUBLIC_FOLDER)
    html = ''.join(f'<li>{f} <a href="/download_public/{f}" class="btn btn-sm btn-primary">下载</a></li>' for f in files)
    return render_template_string(template_base('公共文件', f'<ul>{html}</ul><a href="/upload_public">上传</a>'))

@app.route('/download_public/<filename>')
def download_public(filename):
    write_log('公共下载', filename)
    return send_from_directory(PUBLIC_FOLDER, filename, as_attachment=True)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    error = None
    if request.method == 'POST':
        old = request.form.get('old')
        new = request.form.get('new')
        user = db_query('SELECT * FROM users WHERE username=? AND password=?', [session['username'], old], one=True)
        if user:
            db_query('UPDATE users SET password=? WHERE username=?', [new, session['username']])
            return redirect(url_for('user_upload'))
        error = '原密码错误'
    return render_template_string(template_base('修改密码', '''
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="post">
            <input class="form-control my-2" name="old" type="password" placeholder="原密码" required>
            <input class="form-control my-2" name="new" type="password" placeholder="新密码" required>
            <button class="btn btn-primary">提交</button>
        </form>
    '''), error=error)

@app.route('/delete_account')
@login_required
def delete_account():
    username = session['username']
    folder = os.path.join(UPLOAD_FOLDER, username)
    if os.path.exists(folder):
        for f in os.listdir(folder):
            os.remove(os.path.join(folder, f))
        os.rmdir(folder)
    db_query('DELETE FROM users WHERE username=?', [username])
    session.clear()
    return redirect(url_for('login'))

def template_base(title, content):
    return f'''
    <!DOCTYPE html><html lang="zh"><head>
    <meta charset="UTF-8"><title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>#speedBox{{position:fixed;bottom:10px;right:10px;background:rgba(0,0,0,0.6);color:white;padding:5px 10px;border-radius:10px;font-size:0.9em;}}</style>
    </head><body class="container py-4">
    <h1 class="mb-4">{title}</h1>
    {content}
    <div id="speedBox">网速检测中...</div>
    <script>
    let lastBytes = 0;
    function updateSpeed() {{
        let img = new Image();
        let start = new Date().getTime();
        img.src = '/static/speed-test.png?t=' + start;
        img.onload = function() {{
            let end = new Date().getTime();
            let speed = Math.round(1000 / (end - start) * 8) + 'kbps';
            document.getElementById('speedBox').innerText = '实时网速: ' + speed;
        }}
    }}
    setInterval(updateSpeed, 3000);
    </script>
    </body></html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
