import streamlit as st
from backend import *
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from fpdf import FPDF

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
        sid = st.text_input("Student ID")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            if sid.isdigit():
                user = student_login(int(sid), p)
            else:
                user = None

            if user:
                st.session_state.role = "student"
                st.session_state.sid = int(sid)
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
        query_key = "student_search_query"
        if query_key not in st.session_state:
            st.session_state[query_key] = ""

        query = st.text_input("Enter ", value=st.session_state[query_key], key=query_key)

        suggestions = []
        if query.strip():
            conn = connect_db()
            if filter_type == "Title":
                suggestion_sql = f"SELECT book_id, title, author, shelf_no, available_copies FROM books WHERE title LIKE '%{query}%' AND available_copies > 0 LIMIT 10"
            elif filter_type == "Author":
                suggestion_sql = f"SELECT book_id, title, author, shelf_no, available_copies FROM books WHERE author LIKE '%{query}%' AND available_copies > 0 LIMIT 10"
            else:
                suggestion_sql = f"SELECT book_id, title, author, shelf_no, available_copies FROM books WHERE genre LIKE '%{query}%' AND available_copies > 0 LIMIT 10"

            df_suggestions = pd.read_sql(suggestion_sql, conn)
            conn.close()

            if not df_suggestions.empty:
                st.info("Available books")
                for _, row in df_suggestions.iterrows():
                    st.write(f"🔹 Book ID: {row['book_id']} | {row['title']} | {row['author']} | Available: {row['available_copies']} | Shelf: {row['shelf_no']}")

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
                st.write(f"📘 Book ID: {row['book_id']} | {row['title']} | {row['author']} | Available: {availability} | Shelf: {row['shelf_no']}")

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
            student_id = register_student(name, email, dept, pwd)
            st.success("Student Registered")
            st.info(f"Student ID: {student_id}")

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
        sid_input = st.text_input("Student ID")
        bid_input = st.text_input("Book ID")

        if st.button("Issue"):
            if sid_input.isdigit() and bid_input.isdigit():
                transaction_id = issue_book(int(sid_input), int(bid_input))
                if transaction_id:
                    st.success("Book Issued")

                    conn = connect_db()
                    receipt_sql = """
                        SELECT t.transaction_id, t.issue_date, s.student_id, s.name AS student_name,
                               b.book_id, b.title AS book_name
                        FROM transactions t
                        JOIN students s ON t.student_id = s.student_id
                        JOIN books b ON t.book_id = b.book_id
                        WHERE t.transaction_id = %s
                    """
                    receipt_df = pd.read_sql(receipt_sql, conn, params=(transaction_id,))
                    conn.close()

                    if not receipt_df.empty:
                        receipt = receipt_df.iloc[0]
                        issue_date = pd.to_datetime(receipt['issue_date']).date()
                        due_date = issue_date + pd.Timedelta(days=20)
                        due_date_str = due_date.strftime('%Y-%m-%d')

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(0, 10, 'Library Issue Receipt', ln=True, align='C')
                        pdf.set_font('Arial', '', 12)
                        pdf.ln(5)
                        pdf.cell(0, 8, f"Transaction ID: {receipt['transaction_id']}", ln=True)
                        pdf.cell(0, 8, f"Student Name: {receipt['student_name']}", ln=True)
                        pdf.cell(0, 8, f"Student ID: {receipt['student_id']}", ln=True)
                        pdf.cell(0, 8, f"Book Name: {receipt['book_name']}", ln=True)
                        pdf.cell(0, 8, f"Book ID: {receipt['book_id']}", ln=True)
                        pdf.cell(0, 8, f"Issue Date: {issue_date}", ln=True)
                        pdf.cell(0, 8, f"Due Date (no fine if returned by): {due_date_str}", ln=True)
                        pdf.cell(0, 8, 'Status: issued', ln=True)
                        pdf.ln(5)
                        pdf.multi_cell(0, 8, 'Please return the book by the due date to avoid any fine.')

                        pdf_bytes = pdf.output(dest='S').encode('latin-1')
                        st.download_button(
                            "Download Issue Receipt",
                            pdf_bytes,
                            file_name=f"issue_receipt_{transaction_id}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Unable to load receipt details.")
                else:
                    st.error("Book not available or invalid IDs.")
            else:
                st.error("Enter valid numeric Student ID and Book ID")

    # RETURN
    elif menu == "Return":
        tid_input = st.text_input("Transaction ID")

        if st.button("Return"):
            if tid_input.isdigit():
                return_book(int(tid_input))
                st.success("Book Returned")
            else:
                st.error("Enter a valid numeric Transaction ID")

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