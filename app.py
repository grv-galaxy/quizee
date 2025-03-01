import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import secrets

app = Flask(__name__)

# Load secret key from environment variable for security
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

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
        try:
            cursor.execute("INSERT INTO users (name, username, password) VALUES (?, ?, ?)", (name, username, password))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
        except sqlite3.Error as e:
            flash(f"Registration failed: {e.args[0]}", "error")
        finally:
            conn.close()
        return redirect(url_for('user_login'))
    return render_template('register.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, name FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                session['name'] = user[1]
                return redirect(url_for('select_quiz'))
            flash("Invalid username or password!", "error")
        except sqlite3.Error as e:
            flash(f"Login failed: {e.args[0]}", "error")
        finally:
            conn.close()
    return render_template('user_login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    conn = connect_db()
    cursor = conn.cursor()

    try:
        # Fetch user details
        cursor.execute("SELECT name, username FROM users WHERE id=?", (session['user_id'],))
        user_details = cursor.fetchone()

        # Fetch all scores for the user
        cursor.execute("""
            SELECT e.name AS exam_name, s.name AS subject_name, c.name AS chapter_name, sc.score
            FROM scores sc
            JOIN exams e ON sc.exam_id = e.id
            JOIN chapters c ON sc.chapter_id = c.id
            JOIN subjects s ON c.subject_id = s.id
            WHERE sc.user_id = ?
        """, (session['user_id'],))
        scores = cursor.fetchall()

        # Fetch chapter remarks (example logic)
        cursor.execute("""
            SELECT c.name, AVG(sc.score) AS avg_score
            FROM scores sc
            JOIN chapters c ON sc.chapter_id = c.id
            WHERE sc.user_id = ?
            GROUP BY c.name
        """, (session['user_id'],))
        chapter_remarks = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error fetching profile data: {e.args[0]}", "error")
        user_details = None
        scores = []
        chapter_remarks = []
    finally:
        conn.close()

    return render_template('profile_regestration.html', name=user_details[0] if user_details else None, username=user_details[1] if user_details else None, scores=scores, chapter_remarks=chapter_remarks)

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

    try:
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
    except sqlite3.Error as e:
        flash(f"Error fetching admin data: {e.args[0]}", "error")
        exams, subjects, chapters = [], [], []
        total_exams = total_subjects = total_chapters = total_questions = 0
    finally:
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
    try:
        cursor.execute("INSERT INTO exams (name) VALUES (?)", (exam_name,))
        conn.commit()
        flash("Exam added successfully.", "success")
    except sqlite3.Error as e:
        flash(f"Failed to add exam: {e.args[0]}", "error")
    finally:
        conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/add_subject', methods=['POST'])
def add_subject():
    subject_name = request.form.get('subject_name')
    exam_name = request.form.get('exam_name')  # Get exam name from form
    if not subject_name or not exam_name:
        flash("Please select an exam and enter a subject name.", "error")
        return redirect(url_for('admin_page_modification'))

    exam_id = get_exam_id(exam_name)  # Get exam ID from exam name

    if exam_id is None:
        flash("Invalid exam selected.", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO subjects (name, exam_id) VALUES (?, ?)", (subject_name, exam_id))
        conn.commit()
        flash("Subject added successfully.", "success")
    except sqlite3.Error as e:
        flash(f"Failed to add subject: {e.args[0]}", "error")
    finally:
        conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/add_chapter', methods=['POST'])
def add_chapter():
    chapter_name = request.form.get('chapter_name')
    subject_name = request.form.get('subject_name') # Get subject name from form
    if not chapter_name or not subject_name:
        flash("Please select a subject and enter a chapter name.", "error")
        return redirect(url_for('admin_page_modification'))

    subject_id = get_subject_id(subject_name)  # Get subject ID from subject name

    if subject_id is None:
        flash("Invalid subject selected.", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO chapters (name, subject_id) VALUES (?, ?)", (chapter_name, subject_id))
        conn.commit()
        flash("Chapter added successfully.", "success")
    except sqlite3.Error as e:
        flash(f"Failed to add chapter: {e.args[0]}", "error")
    finally:
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
    chapter_name = request.form.get('chapter_id_question')

    if not question_text or not option1 or not option2 or not option3 or not option4 or not correct_option or not chapter_name:
        flash("Please fill in all question details.", "error")
        return redirect(url_for('admin_page_modification'))

    chapter_id = get_chapter_id(chapter_name)
    if chapter_id is None:
        flash("Invalid chapter selected", "error")
        return redirect(url_for('admin_page_modification'))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO questions (text, option1, option2, option3, option4, correct_option, chapter_id) VALUES (?, ?, ?, ?, ?, ?, ?)", (question_text, option1, option2, option3, option4, correct_option, chapter_id))
        conn.commit()
        flash("Question added successfully", "success")
    except sqlite3.Error as e:
        flash(f"Error adding question: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for('admin_page_modification'))

@app.route('/get_subjects', methods=['POST'])
def get_subjects():
    exam_name = request.form.get('exam_id')
    if not exam_name:
        return jsonify([])

    exam_id = get_exam_id(exam_name)

    if exam_id is None:
        return jsonify([])

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM subjects WHERE exam_id=?", (exam_id,))
        subjects = cursor.fetchall()
        return jsonify([{'id': s[0], 'name': s[1]} for s in subjects])
    except sqlite3.Error:
        return jsonify([])
    finally:
        conn.close()

@app.route('/get_chapters', methods=['POST'])
def get_chapters():
    subject_name = request.form.get('subject_name')
    if not subject_name:
        return jsonify([])

    subject_id = get_subject_id(subject_name)

    if subject_id is None:
        return jsonify([])

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM chapters WHERE subject_id=?", (subject_id,))
        chapters = cursor.fetchall()
        return jsonify([{'id': c[0], 'name': c[1]} for c in chapters])
    except sqlite3.Error:
        return jsonify([])
    finally:
        conn.close()

# ---------------- QUIZ SELECTION ----------------
@app.route('/select_quiz')
def select_quiz():
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, name FROM exams")
        exams = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error fetching quiz data: {e.args[0]}", "error")
        exams = []
    finally:
        conn.close()
    return render_template('select_quiz.html', exams=exams)

@app.route('/show_question', methods=['GET'])
def show_question():
    chapter_id = request.args.get('chapter')
    index = int(request.args.get('current_question_index', 0))
    duration = int(request.args.get('duration', 30))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, text, option1, option2, option3, option4, correct_option FROM questions WHERE chapter_id=?", (chapter_id,))
        questions = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error fetching questions: {e.args[0]}", "error")
        conn.close()
        return redirect(url_for('select_quiz'))

    finally:
        conn.close()
    if questions:
        if index < len(questions):
            question = questions[index]
            return render_template('show_question.html', question=question, index=index, chapter=chapter_id, duration=duration)
        else:
            return redirect(url_for('select_quiz'))
    else:
        flash("No questions available for this chapter.", "error")
        return redirect(url_for('select_quiz'))

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    exam_name = request.form.get('exam')
    subject_name = request.form.get('subject')
    chapter_name = request.form.get('chapter')
    duration = request.form.get('duration')

    if not exam_name or not subject_name or not chapter_name:
        flash("Please select all fields to start the quiz.", "error")
        return redirect(url_for('select_quiz'))

    chapter_id = get_chapter_id(chapter_name)
    if chapter_id is None:
        flash("Invalid chapter selected.", "error")
        return redirect(url_for('select_quiz'))

    return redirect(url_for('show_question', chapter=chapter_id, current_question_index=0, duration=duration))

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    question_id = request.form['question_id']
    selected_answer = request.form['answer']
    index = int(request.form['current_question_index'])
    chapter_id = request.form['chapter']
    duration = int(request.form['duration'])

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT correct_option FROM questions WHERE id=?", (question_id,))
        correct_option = cursor.fetchone()[0]
    except sqlite3.Error as e:
        flash(f"Error fetching correct answer: {e.args[0]}", "error")
        conn.close()
        return redirect(url_for('select_quiz'))
    finally:
        conn.close()

    is_correct = (selected_answer == correct_option)

    if 'correct_answers' not in session:
        session['correct_answers'] = 0

    if is_correct:
        session['correct_answers'] += 1
    flash("Correct!" if is_correct else "Wrong answer!", "success" if is_correct else "error")

    index += 1
    total_questions = total_questions_in_chapter(chapter_id)

    if index < total_questions:
        return redirect(url_for('show_question', chapter=chapter_id, current_question_index=index, duration=duration))
    else:
        correct_answers = session.pop('correct_answers', 0)
        return redirect(url_for('show_result', chapter=chapter_id, correct_answers=correct_answers, total_questions=total_questions))

def total_questions_in_chapter(chapter_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM questions WHERE chapter_id=?", (chapter_id,))
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error:
        return 0
    finally:
        conn.close()

@app.route('/show_result')
def show_result():
    chapter = request.args.get('chapter')
    correct_answers = int(request.args.get('correct_answers', 0))
    total_questions = int(request.args.get('total_questions', 1))
    return render_template('result.html', correct_answers=correct_answers, total_questions=total_questions)

@app.route('/delete_exam', methods=['POST'])
def delete_exam():
    exam_id = request.form['exam_id']
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM subjects WHERE exam_id=?", (exam_id,))
        cursor.execute("DELETE FROM chapters WHERE subject_id IN (SELECT id FROM subjects WHERE exam_id=?)", (exam_id,))
        cursor.execute("DELETE FROM questions WHERE chapter_id IN (SELECT id FROM chapters WHERE subject_id IN (SELECT id FROM subjects WHERE exam_id=?))", (exam_id,))
        cursor.execute("DELETE FROM exams WHERE id=?", (exam_id,))
        conn.commit()
        flash("Exam deleted successfully", "success")
    except sqlite3.Error as e:
        flash(f"Error deleting exam: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('admin_page_modification'))

@app.route('/delete_subject', methods=['POST'])
def delete_subject():
    subject_id = request.form['subject_id']
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM chapters WHERE subject_id=?", (subject_id,))
        cursor.execute("DELETE FROM questions WHERE chapter_id IN (SELECT id FROM chapters WHERE subject_id=?)", (subject_id,))
        cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
        conn.commit()
        flash("Subject deleted successfully", "success")
    except sqlite3.Error as e:
        flash(f"Error deleting subject: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('admin_page_modification'))

@app.route('/delete_chapter', methods=['POST'])
def delete_chapter():
    chapter_id = request.form['chapter_id']
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM questions WHERE chapter_id=?", (chapter_id,))
        cursor.execute("DELETE FROM chapters WHERE id=?", (chapter_id,))
        conn.commit()
        flash("Chapter deleted successfully", "success")
    except sqlite3.Error as e:
        flash(f"Error deleting chapter: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('admin_page_modification'))

@app.route('/delete_question', methods=['POST'])
def delete_question():
    question_id = request.form['question_id']
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM questions WHERE id=?", (question_id,))
        conn.commit()
        flash("Question deleted successfully", "success")
    except sqlite3.Error as e:
        flash(f"Error deleting question: {e}", "error")
    finally:
        conn.close()

    return redirect(url_for('admin_page_modification'))

@app.route('/user_details')
def user_details():
    if not session.get('admin'):
        flash("You must be an admin to view user details.", "error")
        return redirect(url_for('admin_login'))

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, username FROM users")
        users = cursor.fetchall()

        cursor.execute("""
            SELECT u.username, e.name AS exam_name, s.name AS subject_name, c.name AS chapter_name, sc.score
            FROM scores sc
            JOIN users u ON sc.user_id = u.id
            JOIN exams e ON sc.exam_id = e.id
            JOIN subjects s ON sc.subject_id = s.id
            JOIN chapters c ON sc.chapter_id = c.id
        """)
        quiz_results = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error fetching user details: {e}", "error")
        users, quiz_results = [], []
    finally:
        conn.close()

    return render_template('user_details.html', users=users, quiz_results=quiz_results)

# Helper functions to map names to IDs
def get_exam_id(exam_name):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM exams WHERE name=?", (exam_name,))
        exam_id = cursor.fetchone()
        return exam_id[0] if exam_id else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()

def get_subject_id(subject_name):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM subjects WHERE name=?", (subject_name,))
        subject_id = cursor.fetchone()
        return subject_id[0] if subject_id else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()

def get_chapter_id(chapter_name):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM chapters WHERE name=?", (chapter_name,))
        chapter_id = cursor.fetchone()
        return chapter_id[0] if chapter_id else None
    except sqlite3.Error:
        return None
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
