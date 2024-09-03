from flask import Blueprint, render_template, session, request

bp = Blueprint('chat', __name__)

@bp.route('/register', methods=['GET', 'POST'])
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


@bp.route('/login', methods=['GET', 'POST'])
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


@bp.route('/profile')
def profile():
    if 'username' in session:
        return f"Hello, {session['username']}!"
    return redirect(url_for('login'))


@bp.route('/logout')
def logout():
    session.pop('username', None)  # 로그아웃 시 세션에서 사용자 이름 제거
    return redirect(url_for('main'))  # 메인 페이지로 리디렉션


