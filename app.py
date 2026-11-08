import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd
from PIL import Image

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KV No. 2 Mangaluru - Discipline Register",
    page_icon="🏫",
    layout="wide"
)

# --- MODERN UI STYLING (CSS) ---
st.markdown("""
    <style>
    /* Main Header Styling */
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Card Container Styling */
    .css-1r6slb0, .stApp {
        background-color: #f8fafc;
    }
    
    .card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    /* Custom Metric Cards */
    .metric-container {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION STATE SETUP ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

SCHOOL_PASSWORD = "KV2Mangaluru@2026"

# --- LOGIN SCREEN ---
if not st.session_state['authenticated']:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container():
            try:
                logo = Image.open("kv_logo.jpg")
                st.image(logo, width=100)
            except FileNotFoundError:
                pass
                
            st.markdown("## Kendriya Vidyalaya No. 2, Mangaluru")
            st.markdown("### 🔐 Staff Portal Login")
            st.info("Please enter the official school access password.")
            
            entered_password = st.text_input("Password", type="password")
            if st.button("Login to Portal", use_container_width=True, type="primary"):
                if entered_password == SCHOOL_PASSWORD:
                    st.session_state['authenticated'] = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Access denied.")
    st.stop()

# --- SUPABASE API CONNECTION ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# --- HEADER SECTION ---
col_logo, col_title = st.columns([0.8, 5])

with col_logo:
    try:
        logo = Image.open("kv_logo.jpg")
        st.image(logo, width=90)
    except FileNotFoundError:
        st.warning("⚠️ Logo missing.")

with col_title:
    st.markdown("""
        <div class="main-header">
            <h1 style="margin:0; font-size: 22px; color: white;">Kendriya Vidyalaya No. 2, Mangaluru</h1>
            <h3 style="margin:5px 0 0 0; font-size: 14px; color: #cbd5e1; font-weight: normal;">Student Discipline & Incident Management Portal</h3>
        </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Navigation")
menu = st.sidebar.radio("Select Section", [
    "📝 Log New Incident", 
    "🔍 View & Search Records", 
    "✏️ Edit & Delete Records", 
    "📊 Student Report"
])

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state['authenticated'] = False
    st.rerun()

# --- TAB 1: LOG NEW INCIDENT ---
if menu == "📝 Log New Incident":
    st.subheader("Register New Discipline Incident")
    
    with st.form("incident_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            record_date = st.date_input("Incident Date", datetime.date.today())
            adm_no = st.text_input("Admission Number", placeholder="e.g., 4589")
        with col2:
            student_name = st.text_input("Student Full Name", placeholder="e.g., Rahul Sharma")
            reason_option = st.selectbox("Discipline Issue", ["Uniform Issue", "Shoes Issue", "ID Card Missing", "Late Arrival", "Other"])
        
        other_reason = ""
        if reason_option == "Other":
            other_reason = st.text_input("Specify Other Reason", placeholder="Enter specific details...")
        
        submitted = st.form_submit_button("💾 Save Discipline Record", use_container_width=True, type="primary")
        
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
                        supabase.table("discipline_records").insert({
                            "adm_no": adm_no,
                            "student_name": student_name,
                            "reason": final_reason,
                            "record_date": date_str,
                            "record_day": day_str
                        }).execute()
                        st.success(f"✅ Record successfully saved for {student_name} ({day_str}, {date_str})!")
                    except Exception as e:
                        st.error(f"Database error: {e}")

# --- TAB 2: VIEW & SEARCH RECORDS ---
elif menu == "🔍 View & Search Records":
    st.subheader("View, Search & Export Records")
    
    col1, col2 = st.columns(2)
    with col1:
        filter_date = st.date_input("Filter by Date", datetime.date.today())
    with col2:
        search_query = st.text_input("Search Student", placeholder="Type Admission No or Name...")
    
    try:
        if search_query:
            response = supabase.table("discipline_records").select("*").or_(f"adm_no.ilike.%{search_query}%,student_name.ilike.%{search_query}%").order("record_date", desc=True).execute()
        else:
            response = supabase.table("discipline_records").select("*").eq("record_date", filter_date.strftime("%Y-%m-%d")).execute()
            
        records = response.data
        
        if records:
            df = pd.DataFrame([[r['id'], r['adm_no'], r['student_name'], r['reason'], r['record_day'], r['record_date']] for r in records], 
                              columns=["ID", "Admission No", "Student Name", "Reason", "Day", "Date"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Records as CSV", data=csv, file_name="kv_mangalu_discipline_records.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("No discipline records found for the selected criteria.")
            
    except Exception as e:
        st.error(f"Error loading records: {e}")

# --- TAB 3: EDIT & DELETE RECORDS ---
elif menu == "✏️ Edit & Delete Records":
    st.subheader("Edit or Delete Records")
    
    edit_date = st.date_input("Select Date to Manage Records", datetime.date.today())
    
    try:
        response = supabase.table("discipline_records").select("*").eq("record_date", edit_date.strftime("%Y-%m-%d")).order("id", desc=True).execute()
        records = response.data
        
        if not records:
            st.info(f"No discipline records found for {edit_date}.")
        else:
            record_dict = {row['id']: f"ID: {row['id']} | Adm: {row['adm_no']} | Name: {row['student_name']} | Issue: {row['reason']}" for row in records}
            selected_id = st.selectbox(f"Select Record from {edit_date}", options=list(record_dict.keys()), format_func=lambda x: record_dict[x])
            
            single_res = supabase.table("discipline_records").select("*").eq("id", selected_id).execute()
            if single_res.data:
                current = single_res.data[0]
                current_adm, current_name, current_reason, current_date = current['adm_no'], current['student_name'], current['reason'], current['record_date']
                
                st.markdown("---")
                col_edit, col_del = st.columns(2)
                
                with col_edit:
                    st.markdown("#### 🔄 Update Record Details")
                    new_date = st.date_input("Incident Date", datetime.datetime.strptime(str(current_date), "%Y-%m-%d").date())
                    new_adm = st.text_input("Admission No", value=current_adm)
                    new_name = st.text_input("Student Name", value=current_name)
                    
                    default_reasons = ["Uniform Issue", "Shoes Issue", "ID Card Missing", "Late Arrival"]
                    if current_reason in default_reasons:
                        default_idx = default_reasons.index(current_reason)
                        reason_choice = st.selectbox("Discipline Issue", default_reasons + ["Other"], index=default_idx)
                        other_val = ""
                    else:
                        reason_choice = st.selectbox("Discipline Issue", default_reasons + ["Other"], index=4)
                        other_val = current_reason
                        
                    new_other = ""
                    if reason_choice == "Other":
                        new_other = st.text_input("Specify Other Reason", value=other_val)
                    
                    if st.button("Save Changes", use_container_width=True, type="primary"):
                        final_reason = new_other if reason_choice == "Other" else reason_choice
                        if reason_choice == "Other" and not new_other:
                            st.warning("Please specify the 'Other' reason.")
                        else:
                            day_str = new_date.strftime("%A")
                            date_str = new_date.strftime("%Y-%m-%d")
                            
                            try:
                                supabase.table("discipline_records").update({
                                    "adm_no": new_adm,
                                    "student_name": new_name,
                                    "reason": final_reason,
                                    "record_date": date_str,
                                    "record_day": day_str
                                }).eq("id", selected_id).execute()
                                st.success("✅ Record updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating record: {e}")
                                    
                with col_del:
                    st.markdown("#### 🗑️ Remove Record")
                    st.warning("Warning: Deleting a record is permanent.")
                    if st.button("Delete This Record", type="secondary", use_container_width=True):
                        try:
                            supabase.table("discipline_records").delete().eq("id", selected_id).execute()
                            st.success("🗑️ Record deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
                            
    except Exception as e:
        st.error(f"Database error: {e}")

# --- TAB 4: STUDENT INDIVIDUAL REPORT ---
elif menu == "📊 Student Report":
    st.subheader("Individual Student Profile & Report")
    
    search_student = st.text_input("Search Student", placeholder="Enter Admission Number or Name...")
    
    if search_student:
        try:
            response = supabase.table("discipline_records").select("*").or_(f"adm_no.ilike.%{search_student}%,student_name.ilike.%{search_query}%" if 'search_query' in locals() else f"adm_no.ilike.%{search_student}%,student_name.ilike.%{search_student}%").order("record_date", desc=True).execute()
            records = response.data
            
            if records:
                df = pd.DataFrame([[r['id'], r['adm_no'], r['student_name'], r['reason'], r['record_day'], r['record_date']] for r in records], 
                                  columns=["ID", "Admission No", "Student Name", "Reason", "Day", "Date"])
                
                student_name_disp = records[0]['student_name']
                adm_no_disp = records[0]['adm_no']
                
                st.markdown(f"### Student: **{student_name_disp}** (`Adm No: {adm_no_disp}`)")
                
                total_incidents = len(df)
                late_count = len(df[df['Reason'].str.contains("Late", case=False, na=False)])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Incidents", total_incidents)
                with col2:
                    st.metric("Late Arrivals", late_count)
                with col3:
                    most_common = df['Reason'].mode()[0] if not df['Reason'].empty else "N/A"
                    st.metric("Frequent Issue", most_common)
                
                st.markdown("#### Issue Breakdown")
                issue_summary = df['Reason'].value_counts().reset_index()
                issue_summary.columns = ['Discipline Issue', 'Count']
                st.dataframe(issue_summary, use_container_width=True, hide_index=True)
                
                st.markdown("#### Complete History Log")
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    f"📥 Download Report for {student_name_disp}", 
                    data=csv, 
                    file_name=f"student_report_{adm_no_disp}.csv", 
                    mime="text/csv", 
                    use_container_width=True
                )
            else:
                st.warning("No records found matching that search term.")
        except Exception as e:
            st.error(f"Error fetching report: {e}")
