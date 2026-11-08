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
        
        entered_password = st.text_input("Password", type="password")
        if st.button("🔒 Login to Portal", use_container_width=True, type="primary"):
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
    
    if st.button("💾 Save Discipline Record", use_container_width=True, type="primary"):
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
elif menu == "View & Search Records":
    st.subheader("🔍 View, Search & Export Records")
    
    col1, col2 = st.columns(2)
    with col1:
        filter_date = st.date_input("Filter by Date", datetime.date.today())
    with col2:
        search_query = st.text_input("Search Student (Adm No or Name)")
    
    try:
        if search_query:
            response = supabase.table("discipline_records").select("*").or_(f"adm_no.ilike.%{search_query}%,student_name.ilike.%{search_query}%").order("record_date", desc=True).execute()
        else:
            response = supabase.table("discipline_records").select("*").eq("record_date", filter_date.strftime("%Y-%m-%d")).execute()
            
        records = response.data
        
        if records:
            df = pd.DataFrame([[r['id'], r['adm_no'], r['student_name'], r['reason'], r['record_day'], r['record_date']] for r in records], 
                              columns=["ID", "Admission No", "Student Name", "Reason", "Day", "Date"])
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
        response = supabase.table("discipline_records").select("*").eq("record_date", edit_date.strftime("%Y-%m-%d")).order("id", desc=True).execute()
        records = response.data
        
        if not records:
            st.info(f"No discipline records found for {edit_date}. Choose a different date above.")
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
                    st.markdown("### Update Record")
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
                        
                    new_other = ""
                    if reason_choice == "Other":
                        new_other = st.text_input("Specify Other Reason", value=other_val)
                    
                    if st.button("🔄 Update Record", use_container_width=True):
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
                                st.success("✅ Record successfully updated!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error updating record: {e}")
                                    
                with col_del:
                    st.markdown("### Delete Record")
                    st.warning("Warning: Deleting a record is permanent and cannot be undone.")
                    if st.button("🗑️ Delete This Record", type="primary", use_container_width=True):
                        try:
                            supabase.table("discipline_records").delete().eq("id", selected_id).execute()
                            st.success("🗑️ Record deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
                            
    except Exception as e:
        st.error(f"Database error: {e}")
