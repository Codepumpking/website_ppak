"""

Name: app.py (for flask_dashboard)
Author: Codepumpkin
Function: Simple Website with CRUD function for text posts

"""


from flask import Flask, render_template, request, redirect, url_for
import pymysql  #Python MySQL 
import os
from dotenv import load_dotenv 

app = Flask(__name__) #Flask 앱 객체 생성

# DB 연결 function (Docker MySQL)
def get_db_connection():
    return pymysql.connect(
        host= os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password= os.getenv('DB_PASSWORD'),    # 실제 서비스 시에는 환경 변수로 숨겨 놓을 것
        database=os.getenv('DB_NAME'),
        charset='utf8'
    )

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

# 2. 글쓰기 페이지 (Create)
@app.route('/write', methods=['GET', 'POST']) 
# 주소 뒤에 /write가 들어가면 아래 def 함수 실행
# 이 사이트에서 받는 요청은 GET과 POST
def post_write():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # SQL Injection 방지: 파라미터 바인딩(%s)
        cursor.execute("INSERT INTO posts (title, content) VALUES (%s, %s)", (title, content))
        conn.commit()
        conn.close()
        return redirect(url_for('post_list'))
        
    return render_template('write.html')

# 3. 게시글 삭제 (Delete)
@app.route('/delete/<int:id>', methods=['POST'])
def post_delete(id):
    conn = get_db_connection() # DB 연결
    cursor = conn.cursor()

    cursor.execute("DELETE FROM posts WHERE id =%s", (id,)) # 파라미터 바인딩

    conn.commit()
    conn.close()

    return redirect(url_for('post_list'))

# 4. 게시글 수정 (Update)
@app.route('/edit/<int:id>', methods=['GET','POST'])
def post_edit(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST': # = 수정 완료 버튼을 눌렀을때
        # 수정된 내용 전달 받기
        title = request.form['title']
        content = request.form['content'] 
        
        # DB 업데이트 (UPDATE 쿼리 사용)
        cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s", (title, content, id))
        conn.commit()
        conn.close()

        return redirect(url_for('post_list'))

    else: 
        # GET 요청: 기존 글 내용 불러와서 수정 화면에서 보여주기
        cursor.execute("SELECT * FROM posts WHERE id=%s",(id, ))
        post = cursor.fetchone() # 게시글 가져오기
        conn.close()
        return render_template('edit.html', post=post)

if __name__ == '__main__':
    app.run(debug=True)