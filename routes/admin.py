# 관리자 페이지 추가
@app.route('/admin')
def admin():
    cur = mysql_db.connection.cursor()
    cur.execute("SELECT username, email FROM users")
    users = cur.fetchall()
    cur.close()
    return render_template('admin.html', users=users)