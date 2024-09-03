from flask import Blueprint, render_template, session

bp = Blueprint('chat', __name__)

@bp.route('/')
def index():
    username = session.get('username')  # 로그인된 사용자 이름을 세션에서 가져옴
    return render_template('main.html', username=username)  # 메인 페이지 렌더링 시 사용자 이름을 전달

