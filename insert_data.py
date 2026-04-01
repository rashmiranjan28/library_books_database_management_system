import mysql.connector
import random
from faker import Faker
from datetime import timedelta

fake = Faker()

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Rashmi@28",
    database="library_db"
)
cursor = conn.cursor()

# -------------------------------
# 🎓 DEPARTMENTS (IIT ISM STYLE)
# -------------------------------
departments = ["CSE", "ECE", "ME", "EE", "Mining", "Civil"]

# -------------------------------
# 📚 REALISTIC BOOK DATASET
# -------------------------------
book_data = [
    ("Introduction to Algorithms", "Thomas H. Cormen", "CS"),
    ("Operating System Concepts", "Abraham Silberschatz", "CS"),
    ("Database System Concepts", "Henry Korth", "CS"),
    ("Computer Networks", "Andrew Tanenbaum", "CS"),
    ("Artificial Intelligence: A Modern Approach", "Stuart Russell", "AI"),
    ("Machine Learning", "Tom Mitchell", "AI"),
    ("Deep Learning", "Ian Goodfellow", "AI"),
    ("Digital Design", "Morris Mano", "ECE"),
    ("Signals and Systems", "Alan Oppenheim", "ECE"),
    ("Electronic Devices", "Boylestad", "ECE"),
    ("Engineering Mechanics", "Hibbeler", "ME"),
    ("Thermodynamics", "P.K. Nag", "ME"),
    ("Fluid Mechanics", "Fox & McDonald", "ME"),
    ("Strength of Materials", "Bansal", "ME"),
    ("Electrical Engineering Fundamentals", "Vincent Del Toro", "EE"),
    ("Power Systems", "C.L. Wadhwa", "EE"),
    ("Control Systems Engineering", "Nagrath & Gopal", "EE"),
    ("Mining Engineering Handbook", "Howard Hartman", "Mining"),
    ("Rock Mechanics", "Bieniawski", "Mining"),
    ("Geotechnical Engineering", "K.R. Arora", "Civil"),
    ("Structural Analysis", "S.S. Bhavikatti", "Civil"),
    ("Concrete Technology", "M.S. Shetty", "Civil")
]

# -------------------------------
# 👨‍🎓 INSERT 500 STUDENTS
# -------------------------------
for _ in range(500):
    name = fake.name()
    email = name.replace(" ", "").lower() + "@iitism.ac.in"
    dept = random.choice(departments)
    password = "stud123"

    cursor.execute("""
        INSERT INTO students (name, email, department, password)
        VALUES (%s, %s, %s, %s)
    """, (name, email, dept, password))

print("✅ 500 Students Inserted")

# -------------------------------
# 📚 INSERT 2000 BOOKS
# -------------------------------
for _ in range(2000):
    b = random.choice(book_data)

    total = random.randint(5, 25)
    available = random.randint(0, total)
    shelf = random.randint(1, 50)

    cursor.execute("""
        INSERT INTO books (title, author, genre, total_copies, available_copies, shelf_no)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (b[0], b[1], b[2], total, available, shelf))

print("✅ 2000 Books Inserted")

# -------------------------------
# 🔄 INSERT 500 TRANSACTIONS
# -------------------------------
for _ in range(500):
    student_id = random.randint(1, 500)
    book_id = random.randint(1, 2000)

    issue_date = fake.date_between(start_date='-60d', end_date='today')
    returned = random.choice([True, False])

    if returned:
        return_date = issue_date + timedelta(days=random.randint(1, 40))
        days = (return_date - issue_date).days
    else:
        return_date = None
        days = random.randint(1, 60)

    fine = max(0, days - 20)

    cursor.execute("""
        INSERT INTO transactions (student_id, book_id, issue_date, return_date, status, fine)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        student_id,
        book_id,
        issue_date,
        return_date,
        "returned" if returned else "issued",
        fine
    ))

print("✅ 500 Transactions Inserted")

# -------------------------------
# SAVE & CLOSE
# -------------------------------
conn.commit()
conn.close()

print("🎉 ALL DATA INSERTED SUCCESSFULLY")