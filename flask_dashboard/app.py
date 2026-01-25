"""

Name: app.py (for flask_dashboard)
Author: Codepumpkin
Function: Simple Website with CRUD function for text posts

TODO: 
1. 로그인 기능 완성하기 
2. 비밀글 만들기
3. 프로필 (사진 업로드, 다른 사용자 프로필 조회)
4. 아이디, 비밀번호 찾기
"""


from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql  #Python MySQL 
import os
from dotenv import load_dotenv 
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename # 파일 가져오는데 활용

# .env 파일 로드
load_dotenv()

app = Flask(__name__) #Flask 앱 객체 생성
app.secret_key = os.getenv('SECRET_KEY', 'my_secret_key') # 세션을 위한 비밀키


# 로그인 객체
login_manager = LoginManager() #flask_login instance 생성
login_manager.init_app(app) #flask, flask_login 연결
login_manager.login_view = 'login'

# DB 연결 function (Docker MySQL)
def get_db_connection():
    return pymysql.connect(
        host= os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password= os.getenv('DB_PASSWORD'),    # 실제 서비스 시에는 환경 변수로 숨겨 놓을 것
        database=os.getenv('DB_NAME'),
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )

# User Class
class User(UserMixin):
    def __init__(self, id, email, name, affiliation):
        self.id = id
        self.email = email
        self.name = name
        self.affiliation = affiliation
    # 사용자 정보 (id , 이메일, 이름, 소속)
    # 비밀번호는 왜 안넣더라 (?)

    def get_id(self):
        return self.id

    def __repr__(self):
        return f"USER: {self.id} = {self.name}"

# 로그인 =================================================================================

# 로그인이 되어있는지 판단하기 전에 사용자 정보 조회
# return 값은 생성한 사용자 객체
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s ", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        # DB에 있는 정보를 바탕으로 User 객체 생성
        return User(id=user_data['id'], email=user_data['email'], name=user_data['name'], affiliation=user_data['affiliation'])
    return None


# 로그인 페이지(Login)
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        next_page = request.form.get('next')

        conn = get_db_connection()
        cursor = conn.cursor()

        # 사용자 이메일로 찾기
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        conn.close()   # 찾아온 다음에 > 연결 종료 하고, >

        # 사용자 존재 및 비밀번호 확인
        if user_data and user_data['password'] == password:
            user = User(id=user_data['id'], email=user_data['email'], name=user_data['name'], affiliation=user_data['affiliation'])
            login_user(user)
            flash('로그인 성공!', 'success')

            return redirect(next_page if next_page else url_for('post_list'))
        else: 
            flash('이메일 또는 비밀번호가 틀렸습니다.', 'danger')
        
    return render_template('auth/login.html')

# 로그아웃
@app.route('/logout', methods=['GET','POST'])
@login_required # 로그인 후에 사용할 수 있음
def logout():
    logout_user()
    flash('로그아웃 되었습니다.', 'success')
    return redirect(url_for('post_list'))

# 사용자 등록
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 폼 데이터 가져오기 (name 속성 주의)
        user_id = request.form['user_id']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        affiliation = request.form['affiliation']

        conn = get_db_connection()
        cursor = conn.cursor()

        # 중복 체크
        sql = "SELECT * FROM users WHERE id = %s OR email = %s"
        cursor.execute(sql, (user_id, email))
        if cursor.fetchone():
            conn.close()
            flash('이미 존재하는 아이디 또는 이메일입니다.', 'danger')
            return redirect(url_for('register'))

        # DB 저장
        sql_insert = "INSERT INTO users (id, email, name, password, affiliation) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(sql_insert, (user_id, email, name, password, affiliation))
        
        conn.commit()
        conn.close()

        flash('회원가입 완료! 로그인해주세요.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

# =====================================================================================================

# ===== 사용자 관련 ====================================================================================

# 이미지 저장 경로
UPLOAD_FOLDER = 'static/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/profile/<target_id>', methods=['GET', 'POST'])
@login_required
def profile(target_id):
    conn = get_db_connection()
    
    # 내 프로필 수정 요청 (POST)
    if request.method == 'POST' and target_id == current_user.id:
        # 1. 텍스트 정보 수정
        new_school = request.form['school']
        
        # 2. 이미지 업로드 처리
        if 'profile_img' in request.files:
            file = request.files['profile_img']
            if file.filename != '':
                filename = secure_filename(file.filename)
                # static/profile_pics 폴더에 저장
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # DB에는 파일 이름만 저장
                conn.execute('UPDATE users SET profile_img = ? WHERE id = ?', (filename, target_id))

        # 학교 정보 업데이트
        conn.execute('UPDATE users SET school = ? WHERE id = ?', (new_school, target_id))
        conn.commit()
        return redirect(url_for('profile', target_id=target_id))

    # 프로필 조회 (GET)
    user = conn.execute('SELECT * FROM users WHERE id = ?', (target_id,)).fetchone()
    conn.close()
    return render_template('profile.html', user=user, is_mine=(target_id == current_user.id))

# ======================================================================================================

# 1. 게시글 목록 페이지 (Read)
@app.route('/') # default 페이지
def post_list():
    conn = get_db_connection() #DB 연결
    cursor = conn.cursor()
    # ORM 없이 직접 쿼리 작성
    sql = "SELECT * FROM posts ORDER BY id DESC" # 최신 작성 순서대로 나열 
    cursor.execute(sql) # 쿼리 실행
    posts = cursor.fetchall() # 조회된 게시글 전부를 리스트 형태로 리턴 
    conn.close() # 리소스 낭비를 방지하기 위해 연결 종료
    return render_template('list.html', posts=posts)


# 검색 페이지 (Search)
@app.route('/search')
def search():
    # HTML 검색창에서 입력한 단어 가져오기
    keyword = request.args.get('keyword', '')  # 없으면 빈 문자열
    search_type = request.args.get('search_type', 'title') # 기본값은 제목

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_type == 'content':
        sql = "SELECT * FROM posts WHERE content LIKE %s"
        cursor.execute(sql, ('%' + keyword + '%',))
    elif search_type == 'both':
        sql = 'SELECT * FROM posts WHERE title LIKE %s OR content LIKE %s'
        cursor.execute(sql, ('%' + keyword + '%', '%' + keyword + '%'))
    else:
        sql = 'SELECT * FROM posts WHERE title LIKE %s'
        cursor.execute(sql, ('%' + keyword + '%',))
    
    results = cursor.fetchall()
    conn.close()

    return render_template('list.html', posts=results, keyword=keyword, search_type=search_type)


# 글쓰기 페이지 (Create)
@app.route('/write', methods=['GET', 'POST'])
@login_required
def post_write():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        is_secret = 1 if 'is_secret' in request.form else 0
        post_pw = request.form.get('post_pw', '')
        writer_id = current_user.id # 현재 로그인한 사용자 ID 가져오기 (current_user 위에 모듈로 불러옴)

        filename = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join('static/uploads', filename)) # 게시글 파일 저장 폴더

        conn = get_db_connection()
        cursor = conn.cursor()
        # SQL Injection 방지: 파라미터 바인딩(%s)
        # 작성자 ID도 함께 저장
        cursor.execute('INSERT INTO posts (writer_id, title, content, file_path, is_secret, post_password) VALUES (%s, %s, %s, %s, %s, %s)',
                 (writer_id, title, content, filename, is_secret, post_pw))
        conn.commit()
        conn.close()
        return redirect(url_for('post_list'))
        
    return render_template('write.html')

# 3. 게시글 삭제 (Delete)
@app.route('/delete/<int:id>', methods=['POST'])
@login_required # 본인이 작성한 글만 삭제 가능
def post_delete(id):
    conn = get_db_connection() # DB 연결
    cursor = conn.cursor()

    cursor.execute("SELECT writer_id FROM posts WHERE id = %s", (id,))
    post = cursor.fetchone()

    if post and post['writer_id'] == current_user.id:
        cursor.execute("DELETE FROM posts WHERE id = %s", (id, )) # 파라미터 바인딩
        conn.commit()
        flash('게시글이 삭제되었습니다.', 'success')
    else:
        flash('본인이 작성한 글만 삭제할 수 있습니다', 'danger')

    conn.close()
    return redirect(url_for('post_list'))


# 게시글 수정 (Update)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def post_edit(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 게시글 가져오기
    cursor.execute("SELECT * FROM posts WHERE id = %s", (id,))
    post = cursor.fetchone()

    # 글이 없거나, 작성자 != 현재 사용자 이면 접근 불가
    if not post or post['writer_id'] != current_user.id:
        conn.close()
        flash('수정 권한이 없습니다.', 'danger')
        return redirect(url_for('post_list'))

    if request.method == 'POST': # 수정 완료 버튼 눌렀을 때
        #  폼에서 수정된 내용 가져오기
        title = request.form['title']
        content = request.form['content']

        # 비밀글 체크 
        is_secret = 1 if 'is_secret' in request.form else 0

        # 비밀번호: 없으면 기본값 ''
        post_pw = request.form.get('post_pw', '')

    # 파일 처리 로직
        # 기본값은 '기존 파일명'으로 설정
        final_filename = post['file_path']

        # 새 파일 업로드 -> 기존 파일 대체
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # 새 파일 저장
                filename = secure_filename(file.filename)
                save_path = os.path.join('static/uploads', filename)
                file.save(save_path)
                # DB에 넣을 파일명을 교체
                final_filename = filename

        # DB 업데이트
        sql = """
            UPDATE posts 
            SET title=%s, content=%s, file_path=%s, is_secret=%s, post_password=%s 
            WHERE id=%s
        """
        cursor.execute(sql, (title, content, final_filename, is_secret, post_pw, id))
        conn.commit()
        conn.close()
        
        # 이후에 해당글 상세 페이지로 이동
        return redirect(url_for('post_detail', post_id=id))

    else: 
        # GET 요청: 수정 화면 보여주기
        conn.close()
        return render_template('edit.html', post=post)

# 비밀글 비밀번호 확인
@app.route('/check_password/<int:post_id>', methods=['GET', 'POST'])
def check_password_view(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    conn.close()

    if not post:
        flash('존재하지 않는 게시글입니다.', 'danger')
        return redirect(url_for('post_list'))

    if request.method == 'POST':
        input_pw = request.form.get('password')
        # 비밀번호가 일치하면 -> detail.html 게시글 페이지로 이동
        if input_pw == post['post_password']:
            return render_template('detail.html', post=post)
        else:
            flash('비밀번호가 틀렸습니다.', 'danger')
            return redirect(url_for('check_password_view', post_id=post_id))

    # 2. GET: 처음 들어왔을때
    return render_template('check_password.html', post=post)

# 상세 페이지 보기 (일반글 또는 비밀번호 통과 후)
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
    post = cursor.fetchone()
    conn.close()
    
    if post['is_secret'] == 1:
        if not current_user.is_authenticated or current_user.id != post['writer_id']:
            return redirect(url_for('check_password_view', post_id=post_id))

    return render_template('detail.html', post=post)


if __name__ == '__main__':
    app.run(debug=True)