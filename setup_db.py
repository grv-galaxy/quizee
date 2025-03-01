import sqlite3

DB_NAME = "quiz_app.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create users table
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)''')

# Create exams table
cursor.execute('''CREATE TABLE IF NOT EXISTS exams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
)''')

# Create subjects table
cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    exam_id INTEGER NOT NULL,
    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE
)''')

# Create chapters table
cursor.execute('''CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
)''')

# Create questions table
cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    correct_option TEXT NOT NULL,
    chapter_id INTEGER NOT NULL,
    FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE
)''')

# Create scores table
cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    chapter_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters (id) ON DELETE CASCADE
)''')

conn.commit()
conn.close()

print("Database setup completed successfully!")
