import streamlit as st
import sqlite3
import datetime
import pandas as pd
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KV No. 2 Mangaluru - Discipline Register",
    page_icon="🏫",
    layout="wide"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION STATE SETUP ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- SCHOOL ACCESS PASSWORD ---
SCHOOL_PASSWORD = "KV2Mangaluru@2026"

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            logo = Image.open("kv_logo.jpg")
            st.image(logo, width=120)
        except FileNotFoundError:
            pass
            
        st.markdown("## Kendriya Vidyalaya No. 2, Mangaluru")
        st.markdown("### Restricted Staff Portal")
        st.info("Please enter the official school access password to proceed.")
        
        with st.form("login_form"):
            entered_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("🔒 Login to Portal", use_container_width=True)
            
            if submit_login:
                if entered_password == SCHOOL_PASSWORD:
                    st.session_state['authenticated'] = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Access denied.")
    st.stop()

# --- SQLITE DATABASE SETUP ---
DB_NAME = "school_discipline.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discipline_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adm_no TEXT NOT NULL,
            student_name TEXT NOT NULL,
            reason TEXT NOT NULL,
            record_date TEXT NOT NULL,
            record_day TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- HEADER SECTION WITH LOGO & SCHOOL NAME ---
col_logo, col_title = st.columns([1, 5])

with col_logo:
    try:
        logo = Image.open("kv_logo.jpg")
        st.image(logo, width=100)
    except FileNotFoundError:
        st.warning("⚠️ Logo 'kv_logo.jpg' not found in folder.")

with col_title:
    st.markdown("""
        <div class="main-header">
            <h1 style="margin:0; font-size: 24px; color: white;">Kendriya Vidyalaya No. 2, Mangaluru</h1>
            <h3 style="margin:5px 0 0 0; font-size: 15px; color: #e2e8f0; font-weight: normal;">Student Discipline & Incident Management Portal</h3>
        </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION & LOGOUT ---
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Select Option", ["Log New Incident", "View & Search Records", "Edit & Delete Records"])

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state['authenticated'] = False
    st.rerun()

# --- TAB 1: LOG NEW INCIDENT ---
if menu == "Log New Incident":
    st.subheader("📝 Register New Discipline Incident")
    
    with st.form("incident_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            record_date = st.date_input("Incident Date", datetime.date.today())
            adm_no = st.text_input("Admission No")
        with col2:
            student_name = st.text_input("Student Name")
            reason_option = st.selectbox("Discipline Issue", ["Uniform Issue", "Shoes Issue", "ID Card Missing", "Other"])
        
        other_reason = ""
        if reason_option == "Other":
            other_reason = st.text_input("Please specify the 'Other' reason")
        
        submitted = st.form_submit_button("💾 Save Discipline Record", use_container_width=True)
        
        if submitted:
            if not adm_no or not student_name:
                st.warning("Please fill in both Admission No and Student Name.")
            else:
                final_reason = other_reason if reason_option == "Other" else reason_option
                if reason_option == "Other" and not other_reason:
                    st.warning("Please specify the 'Other' reason.")
                else:
                    day_str = record_date.strftime("%A")
                    date_str = record_date.strftime("%Y-%m-%d")
                    
                    try:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO discipline_records (adm_no, student_name, reason, record_date, record_day) VALUES (?, ?, ?, ?, ?)",
                            (adm_no, student_name, final_reason, date_str, day_str)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Record successfully saved for {student_name} ({day_str}, {date_str})!")
                    except Exception as e:
                        st.error(f"Database error: {e}")

# --- TAB 2: VIEW & SEARCH RECORDS ---
elif menu == "View & Search Records":
    st.subheader("🔍 View, Search & Export Records")
    
    col1, col2 = st.columns(2)
    with col1:
        filter_date = st.date_input("Filter by Date", datetime.date.today())
    with col2:
        search_query = st.text_input("Search Student (Adm No or Name)")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        if search_query:
            cursor.execute(
                "SELECT id, adm_no, student_name, reason, record_day, record_date FROM discipline_records WHERE adm_no LIKE ? OR student_name LIKE ? ORDER BY record_date DESC",
                (f"%{search_query}%", f"%{search_query}%")
            )
        else:
            cursor.execute(
                "SELECT id, adm_no, student_name, reason, record_day, record_date FROM discipline_records WHERE record_date = ?",
                (filter_date.strftime("%Y-%m-%d"),)
            )
            
        records = cursor.fetchall()
        conn.close()
        
        if records:
            df = pd.DataFrame(records, columns=["ID", "Admission No", "Student Name", "Reason", "Day", "Date"])
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Records as CSV", data=csv, file_name="kv_mangalu_discipline_records.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("No discipline records found for the selected criteria.")
            
    except Exception as e:
        st.error(f"Error loading records: {e}")

# --- TAB 3: EDIT & DELETE RECORDS (CALENDAR DRIVEN) ---
elif menu == "Edit & Delete Records":
    st.subheader("✏️ Edit or Delete Records by Date")
    
    edit_date = st.date_input("Select Calendar Date to Manage Records", datetime.date.today())
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT id, adm_no, student_name, reason, record_date FROM discipline_records WHERE record_date = ? ORDER BY id DESC", (edit_date.strftime("%Y-%m-%d"),))
        records = cursor.fetchall()
        conn.close()
        
        if not records:
            st.info(f"No discipline records found for {edit_date}. Choose a different date above.")
        else:
            record_dict = {row[0]: f"ID: {row[0]} | Adm: {row[1]} | Name: {row[2]} | Issue: {row[3]}" for row in records}
            selected_id = st.selectbox(f"Select Record from {edit_date}", options=list(record_dict.keys()), format_func=lambda x: record_dict[x])
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT adm_no, student_name, reason, record_date FROM discipline_records WHERE id = ?", (selected_id,))
            selected_data = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if selected_data:
                current_adm, current_name, current_reason, current_date = selected_data
                
                st.markdown("---")
                col_edit, col_del = st.columns(2)
                
                with col_edit:
                    st.markdown("### Update Record")
                    with st.form("edit_form"):
                        new_date = st.date_input("Incident Date", datetime.datetime.strptime(str(current_date), "%Y-%m-%d").date())
                        new_adm = st.text_input("Admission No", value=current_adm)
                        new_name = st.text_input("Student Name", value=current_name)
                        
                        default_reasons = ["Uniform Issue", "Shoes Issue", "ID Card Missing"]
                        if current_reason in default_reasons:
                            default_idx = default_reasons.index(current_reason)
                            reason_choice = st.selectbox("Discipline Issue", default_reasons + ["Other"], index=default_idx)
                            other_val = ""
                        else:
                            reason_choice = st.selectbox("Discipline Issue", default_reasons + ["Other"], index=3)
                            other_val = current_reason.replace("Other: ", "") if current_reason.startswith("Other: ") else current_reason
                            
                        new_other = st.text_input("Specify Other Reason", value=other_val if reason_choice == "Other" else "")
                        
                        update_submitted = st.form_submit_button("🔄 Update Record", use_container_width=True)
                        
                        if update_submitted:
                            final_reason = new_other if reason_choice == "Other" else reason_choice
                            if reason_choice == "Other" and not new_other:
                                st.warning("Please specify the 'Other' reason.")
                            else:
                                day_str = new_date.strftime("%A")
                                date_str = new_date.strftime("%Y-%m-%d")
                                
                                try:
                                    conn = sqlite3.connect(DB_NAME)
                                    cursor = conn.cursor()
                                    cursor.execute(
                                        "UPDATE discipline_records SET adm_no = ?, student_name = ?, reason = ?, record_date = ?, record_day = ? WHERE id = ?",
                                        (new_adm, new_name, final_reason, date_str, day_str, selected_id)
                                    )
                                    conn.commit()
                                    cursor.close()
                                    conn.close()
                                    st.success("✅ Record successfully updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating record: {e}")
                                    
                with col_del:
                    st.markdown("### Delete Record")
                    st.warning("Warning: Deleting a record is permanent and cannot be undone.")
                    if st.button("🗑️ Delete This Record", type="primary", use_container_width=True):
                        try:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM discipline_records WHERE id = ?", (selected_id,))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success("🗑️ Record deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
                            
    except Exception as e:
        st.error(f"Database error: {e}")