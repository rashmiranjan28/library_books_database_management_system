import mysql.connector
from datetime import date

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rashmi@28",
        database="library_db"
    )

# LOGIN
def admin_login(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s",
                   (username, password))
    res = cursor.fetchone()
    conn.close()
    return res

def student_login(student_id, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id=%s AND password=%s",
                   (student_id, password))
    res = cursor.fetchone()
    conn.close()
    return res

# REGISTER
def register_student(name, email, dept, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students (name, email, department, password)
        VALUES (%s, %s, %s, %s)
    """, (name, email, dept, password))
    conn.commit()
    conn.close()

# BOOK SEARCH
def search_book(title):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE title LIKE %s", (f"%{title}%",))
    data = cursor.fetchall()
    conn.close()
    return data

# ISSUE
def issue_book(student_id, book_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT available_copies FROM books WHERE book_id=%s", (book_id,))
    available = cursor.fetchone()[0]

    if available > 0:
        cursor.execute("""
            INSERT INTO transactions (student_id, book_id, issue_date, status, fine)
            VALUES (%s, %s, CURDATE(), 'issued', 0)
        """, (student_id, book_id))

        cursor.execute("""
            UPDATE books SET available_copies = available_copies - 1
            WHERE book_id=%s
        """, (book_id,))

        conn.commit()

    conn.close()

# RETURN
def return_book(tid):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT issue_date, book_id FROM transactions WHERE transaction_id=%s", (tid,))
    issue_date, book_id = cursor.fetchone()

    today = date.today()
    days = (today - issue_date).days
    fine = max(0, days - 20)

    cursor.execute("""
        UPDATE transactions
        SET return_date=%s, status='returned', fine=%s
        WHERE transaction_id=%s
    """, (today, fine, tid))

    cursor.execute("""
        UPDATE books SET available_copies = available_copies + 1
        WHERE book_id=%s
    """, (book_id,))

    conn.commit()
    conn.close()