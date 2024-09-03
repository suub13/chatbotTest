from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector  # MySQL 데이터베이스 설정을 위한 모듈

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL 설정
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'subyou'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'mywebsite'

mysql_db = MySQL(app)


def run_sql_script(script_path):
    with open(script_path, 'r') as file:
        sql_script = file.read()

    conn = mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD']
    )

    cursor = conn.cursor()
    try:
        for result in cursor.execute(sql_script, multi=True):
            if result.with_rows:
                print("Rows produced by statement '{}':".format(result.statement))
                print(result.fetchall())
            else:
                print("Number of rows affected by statement '{}': {}".format(result.statement, result.rowcount))
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# 애플리케이션 시작 시 SQL 스크립트 실행
run_sql_script('setup.sql')


@app.route('/')
def main():
    username = session.get('username')  # 로그인된 사용자 이름을 세션에서 가져옴
    return render_template('main.html', username=username)  # 메인 페이지 렌더링 시 사용자 이름을 전달


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # 해시 알고리즘을 명확히 지정
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cur = mysql_db.connection.cursor()
        try:
            # 사용자 이름과 이메일 중복 확인
            cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cur.fetchone()
            if existing_user:
                flash('Username or email already exists. Please choose a different one.')
                return render_template('register.html')

            # 중복이 없을 경우에만 사용자 추가
            cur.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
                        (username, hashed_password, email))
            mysql_db.connection.commit()
            flash('Registration successful! You can now log in.')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {e}')
            return render_template('register.html')
        finally:
            cur.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql_db.connection.cursor()
        try:
            cur.execute("SELECT * FROM users WHERE username = %s", [username])
            user = cur.fetchone()
            if user is None:
                return render_template('login.html', username_error='Username does not exist.')

            if check_password_hash(user[2], password):
                session['username'] = user[1]  # 로그인 성공 시 세션에 사용자 이름 저장
                return redirect(url_for('main'))  # 메인 페이지로 리디렉션
            else:
                return render_template('login.html', password_error='Invalid password.')
        except Exception as e:
            flash('Database error: {}'.format(e))
            return render_template('login.html')
        finally:
            cur.close()
    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'username' in session:
        return f"Hello, {session['username']}!"
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)  # 로그아웃 시 세션에서 사용자 이름 제거
    return redirect(url_for('main'))  # 메인 페이지로 리디렉션


# 관리자 페이지 추가
@app.route('/admin')
def admin():
    cur = mysql_db.connection.cursor()
    cur.execute("SELECT username, email FROM users")
    users = cur.fetchall()
    cur.close()
    return render_template('admin.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
