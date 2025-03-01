import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import secrets

app = Flask(__name__)

# Load secret key from environment variable for security
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)  # Fallback for local testing

# Database configuration
DB_NAME = "quiz_app.db"

def connect_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 5000")  
    return conn

@app.route('/')
def home():
    return render_template('login.html')

# ---------------- USER AUTHENTICATION ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, username, password) VALUES (?, ?, ?)", (name, username, password))
        conn.commit()
        conn.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('user_login'))
    return render_template('register.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            return redirect(url_for('select_quiz'))
        flash("Invalid username or password!", "error")
    return render_template('user_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))
    return render_template('profile_registration.html', name=session['name'])

# ---------------- ADMIN AUTHENTICATION ----------------
ADMIN_ID = "GauravKumar@123"
ADMIN_PASSWORD = "Thakur@098"

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['admin_id'] == ADMIN_ID and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_page_modification'))
        flash("Invalid Admin ID or Password", "error")
    return render_template('admin_login.html')

@app.route('/admin_page_modification')
def admin_page_modification():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM exams")
    exams = cursor.fetchall()

    cursor.execute("SELECT id, name, exam_id FROM subjects")
    subjects = cursor.fetchall()

    cursor.execute("SELECT id, name, subject_id FROM chapters")
    chapters = cursor.fetchall()

    # Fetch counts
    cursor.execute("SELECT COUNT(*) FROM exams")
    total_exams = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM chapters")
    total_chapters = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'admin_page_modification.html',
        exams=exams, subjects=subjects, chapters=chapters,
        total_exams=total_exams, total_subjects=total_subjects,
        total_chapters=total_chapters, total_questions=total_questions
    )

@app.route('/add_exam', methods=['POST'])
def add_exam():
    exam_name = request.form.get('exam_name')
    if not exam_name:
        flash("Please enter an exam name.", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO exams (name) VALUES (?)", (exam_name,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form.get('subject_name')
    exam_id = request.form.get('exam_id')
    if not subject_name or not exam_id:
        flash("Please select an exam and enter a subject name.", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subjects (name, exam_id) VALUES (?, ?)", (subject_name, exam_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/add_chapter', methods=['POST'])
def add_chapter():
    chapter_name = request.form.get('chapter_name')
    subject_id = request.form.get('subject_id')
    if not chapter_name or not subject_id:
        flash("Please select a subject and enter a chapter name.", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chapters (name, subject_id) VALUES (?, ?)", (chapter_name, subject_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/add_question', methods=['POST'])
def add_question():
    question_text = request.form.get('question_text')
    option1 = request.form.get('option1')
    option2 = request.form.get('option2')
    option3 = request.form.get('option3')
    option4 = request.form.get('option4')
    correct_option = request.form.get('correct_option')
    chapter_id = request.form.get('chapter_id_question')

    if not question_text or not option1 or not option2 or not option3 or not option4 or not correct_option or not chapter_id:
        flash("Please fill in all question details.", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO questions (text, option1, option2, option3, option4, correct_option, chapter_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (question_text, option1, option2, option3, option4, correct_option, chapter_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/get_subjects', methods=['POST'])
def get_subjects():
    exam_id = request.form.get('exam_id')
    if not exam_id:
        return jsonify([])

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM subjects WHERE exam_id=?", (exam_id,))
    subjects = cursor.fetchall()
    conn.close()
    return jsonify([{'id': s[0], 'name': s[1]} for s in subjects])

@app.route('/get_chapters', methods=['POST'])
def get_chapters():
    subject_id = request.form.get('subject_id')
    if not subject_id:
        return jsonify([])

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM chapters WHERE subject_id=?", (subject_id,))
    chapters = cursor.fetchall()
    conn.close()
    return jsonify([{'id': c[0], 'name': c[1]} for c in chapters])

# ---------------- QUIZ SELECTION ----------------
@app.route('/select_quiz')
def select_quiz():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM exams")
    exams = cursor.fetchall()

    cursor.execute("SELECT subjects.id, subjects.name, exams.name FROM subjects JOIN exams ON subjects.exam_id = exams.id")
    subjects = cursor.fetchall()

    cursor.execute("SELECT chapters.id, chapters.name, subjects.name FROM chapters JOIN subjects ON chapters.subject_id = subjects.id")
    chapters = cursor.fetchall()

    conn.close()
    return render_template('select_quiz.html', exams=exams, subjects=subjects, chapters=chapters)

@app.route('/show_question', methods=['GET'])
def show_question():
    chapter_id = request.args.get('chapter')
    index = int(request.args.get('current_question_index', 0))
    duration = int(request.args.get('duration', 30))  # Get duration from query parameters

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, option1, option2, option3, option4, correct_option FROM questions WHERE chapter_id=?", (chapter_id,))
    questions = cursor.fetchall()
    conn.close()

    if questions:
        if index < len(questions):
            question = questions[index]
            # Printing all values of question for debugging
            print("Printing all the values for the current question")
            for value in question:
                print(value)
            return render_template('show_question.html', question=question, index=index, chapter=chapter_id, duration = duration) # Make sure to pass duration
        else:
            # Handle end of quiz
            return redirect(url_for('select_quiz'))
    else:
        # Handle no questions
        flash("No questions available for this chapter.", "error")
        return redirect(url_for('select_quiz'))

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    exam = request.form.get('exam')
    subject = request.form.get('subject')
    chapter = request.form.get('chapter')
    duration = request.form.get('duration')

    if not exam or not subject or not chapter:
        flash("Please select all fields to start the quiz.", "error")
        return redirect(url_for('select_quiz'))

    # Assuming you have a way to get chapter_id from chapter name
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chapters WHERE name=?", (chapter,))
    chapter_id = cursor.fetchone()[0]
    conn.close()

    return redirect(url_for('show_question', chapter=chapter_id, current_question_index=0, duration = duration)) # Make sure to add duration

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    question_id = request.form['question_id']
    selected_answer = request.form['answer']
    index = int(request.form['current_question_index'])
    chapter_id = request.form['chapter']
    duration = int(request.form['duration'])

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT correct_option FROM questions WHERE id=?", (question_id,))
    correct_option = cursor.fetchone()[0]
    conn.close()

    is_correct = (selected_answer == correct_option)

    if 'correct_answers' not in session:
        session['correct_answers'] = 0

    if is_correct:
        flash("Correct!", "success")
        session['correct_answers'] += 1
    else:
        flash("Wrong answer!", "error")

    index += 1
    total_questions = total_questions_in_chapter(chapter_id) # Getting the value of total questions of that chapter

    if index < total_questions:
        return redirect(url_for('show_question', chapter=chapter_id, current_question_index=index, duration = duration))
    else:
        # Quiz is finished, redirect to results
        correct_answers = session.pop('correct_answers', 0)  # Get the number of correct answer that was there in session
        total_questions = total_questions_in_chapter(chapter_id)
        return redirect(url_for('show_result', chapter=chapter_id, correct_answers=correct_answers, total_questions = total_questions))

def total_questions_in_chapter(chapter_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions WHERE chapter_id=?", (chapter_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

@app.route('/show_result')
def show_result():
    chapter = request.args.get('chapter')
    correct_answers = int(request.args.get('correct_answers', 0))
    total_questions = int(request.args.get('total_questions', 1))
    return render_template('result.html', correct_answers=correct_answers, total_questions=total_questions)

from flask import request, redirect, url_for

# Assuming you have a database connection function named `connect_db()`

@app.route('/delete_exam', methods=['POST'])
def delete_exam():
    exam_id = request.form['exam_id']
    conn = connect_db()
    cursor = conn.cursor()
    
    # Delete subjects and chapters associated with the exam
    cursor.execute("DELETE FROM subjects WHERE exam_id=?", (exam_id,))
    cursor.execute("DELETE FROM chapters WHERE subject_id IN (SELECT id FROM subjects WHERE exam_id=?)", (exam_id,))
    cursor.execute("DELETE FROM questions WHERE chapter_id IN (SELECT id FROM chapters WHERE subject_id IN (SELECT id FROM subjects WHERE exam_id=?))", (exam_id,))
    
    # Delete the exam itself
    cursor.execute("DELETE FROM exams WHERE id=?", (exam_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_page_modification'))

@app.route('/delete_subject', methods=['POST'])
def delete_subject():
    subject_id = request.form['subject_id']
    conn = connect_db()
    cursor = conn.cursor()
    
    # Delete chapters and questions associated with the subject
    cursor.execute("DELETE FROM questions WHERE chapter_id IN (SELECT id FROM chapters WHERE subject_id=?)", (subject_id,))
    cursor.execute("DELETE FROM chapters WHERE subject_id=?", (subject_id,))
    
    # Delete the subject itself
    cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_page_modification'))

@app.route('/delete_chapter', methods=['POST'])
def delete_chapter():
    chapter_id = request.form['chapter_id']
    conn = connect_db()
    cursor = conn.cursor()
    
    # Delete questions associated with the chapter
    cursor.execute("DELETE FROM questions WHERE chapter_id=?", (chapter_id,))
    
    # Delete the chapter itself
    cursor.execute("DELETE FROM chapters WHERE id=?", (chapter_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_page_modification'))

@app.route('/delete_question', methods=['POST'])
def delete_question():
    question_id = request.form['question_id']
    conn = connect_db()
    cursor = conn.cursor()
    
    # Delete the question itself
    cursor.execute("DELETE FROM questions WHERE id=?", (question_id,))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_page_modification'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) # Get port from environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=False)  # Listen on all public IPs (0.0.0.0)
