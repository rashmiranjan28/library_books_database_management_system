import streamlit as st
from backend import *
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="Library System", layout="wide")

if "role" not in st.session_state:
    st.session_state.role = None

# =========================
# 🔐 LOGIN PAGE
# =========================
if st.session_state.role is None:
    st.title("📚 Library Login System")

    role = st.selectbox("Login As", ["Admin", "Student"])

    if role == "Admin":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if admin_login(u, p):
                st.session_state.role = "admin"
                st.success("Welcome Admin")
            else:
                st.error("Invalid Credentials")

    else:
        sid = st.number_input("Student ID")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            user = student_login(sid, p)
            if user:
                st.session_state.role = "student"
                st.session_state.sid = sid
                st.success("Login Successful")
            else:
                st.error("❌ Not found. Contact Admin")

# =========================
# 👨‍🎓 STUDENT PANEL
# =========================
elif st.session_state.role == "student":

    st.sidebar.title("Student Panel")
    menu = st.sidebar.selectbox("Menu", ["Search Books", "My Books", "Logout"])

    # 🚨 ALERTS AFTER LOGIN
    conn = connect_db()
    df_alert = pd.read_sql(f"""
        SELECT * FROM transactions
        WHERE student_id={st.session_state.sid} AND status='issued'
    """, conn)

    today = pd.to_datetime(date.today())

    for _, row in df_alert.iterrows():
        issue_date = pd.to_datetime(row['issue_date'])
        days = (today - issue_date).days

        if days > 20:
            st.error(f"⚠️ Fine Running: ₹{days-20} (Book ID {row['book_id']})")
        elif days >= 15:
            st.warning(f"⚠️ Return Soon! Only {20-days} days left (Book ID {row['book_id']})")

    # 🔍 SEARCH WITH FILTERS
    if menu == "Search Books":
        st.subheader("🔍 Search Books")

        filter_type = st.selectbox("Filter By", ["Title", "Author", "Genre"])
        query = st.text_input("Enter value")

        if st.button("Search"):
            conn = connect_db()

            if filter_type == "Title":
                sql = f"SELECT * FROM books WHERE title LIKE '%{query}%'"
            elif filter_type == "Author":
                sql = f"SELECT * FROM books WHERE author LIKE '%{query}%'"
            else:
                sql = f"SELECT * FROM books WHERE genre LIKE '%{query}%'"

            df = pd.read_sql(sql, conn)

            for _, row in df.iterrows():
                availability = "Yes" if row['available_copies'] > 0 else "No"
                st.write(f"📘 {row['title']} | {row['author']} | Available: {availability} | Shelf: {row['shelf_no']}")

    elif menu == "My Books":
        df = pd.read_sql(f"""
            SELECT * FROM transactions WHERE student_id={st.session_state.sid}
        """, conn)

        st.dataframe(df)

    elif menu == "Logout":
        st.session_state.role = None

# =========================
# 👨‍💼 ADMIN PANEL
# =========================
elif st.session_state.role == "admin":

    st.sidebar.title("Admin Panel")
    menu = st.sidebar.selectbox("Menu", [
        "Register Student", "Search Books",
        "Issue", "Return", "Analytics", "Logout"
    ])

    # 👨‍🎓 REGISTER
    if menu == "Register Student":
        st.subheader("Register Student")

        name = st.text_input("Name")
        email = st.text_input("Email")
        dept = st.selectbox("Dept", ["CSE", "ECE", "ME", "EE", "Mining", "Civil"])
        pwd = st.text_input("Password")

        if st.button("Register"):
            register_student(name, email, dept, pwd)
            st.success("Student Registered")

    # 🔍 SEARCH
    elif menu == "Search Books":
        filter_type = st.selectbox("Filter By", ["Title", "Author", "Genre"])
        query = st.text_input("Enter value")

        if st.button("Search"):
            conn = connect_db()

            if filter_type == "Title":
                sql = f"SELECT * FROM books WHERE title LIKE '%{query}%'"
            elif filter_type == "Author":
                sql = f"SELECT * FROM books WHERE author LIKE '%{query}%'"
            else:
                sql = f"SELECT * FROM books WHERE genre LIKE '%{query}%'"

            df = pd.read_sql(sql, conn)
            st.dataframe(df)

    # ISSUE
    elif menu == "Issue":
        sid = st.number_input("Student ID")
        bid = st.number_input("Book ID")

        if st.button("Issue"):
            issue_book(sid, bid)
            st.success("Book Issued")

    # RETURN
    elif menu == "Return":
        tid = st.number_input("Transaction ID")

        if st.button("Return"):
            return_book(tid)
            st.success("Book Returned")

    # 📊 ANALYTICS + ML
    elif menu == "Analytics":

        conn = connect_db()
        df = pd.read_sql("SELECT * FROM transactions", conn)

        st.subheader("📊 Issue vs Return")
        status_counts = df['status'].value_counts()

        fig, ax = plt.subplots()
        ax.bar(status_counts.index, status_counts.values)
        ax.set_xlabel("Status")
        ax.set_ylabel("Count")
        ax.set_title("Issue vs Return")
        st.pyplot(fig)

        # 📈 MONTHLY FINE TREND
        df['issue_date'] = pd.to_datetime(df['issue_date'])
        df['month'] = df['issue_date'].dt.to_period('M')

        fine_trend = df.groupby('month')['fine'].sum()

        st.subheader("📈 Monthly Fine Trend")

        fig2, ax2 = plt.subplots()
        fine_trend.plot(ax=ax2)
        ax2.set_xlabel("Month")
        ax2.set_ylabel("Total Fine")
        ax2.set_title("Monthly Fine Trend")
        st.pyplot(fig2)

        # 🤖 ML: MOST DEMANDED BOOKS
        st.subheader("🤖 Predicted Popular Books Next Week")

        book_counts = df['book_id'].value_counts().head(10)

        fig3, ax3 = plt.subplots()
        ax3.bar(book_counts.index.astype(str), book_counts.values)
        ax3.set_xlabel("Book ID")
        ax3.set_ylabel("Times Issued")
        ax3.set_title("Top Demanded Books")
        st.pyplot(fig3)

        st.info("📌 These books are likely to be issued next week → Keep more copies available.")

    elif menu == "Logout":
        st.session_state.role = None