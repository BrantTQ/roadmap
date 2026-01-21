import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Roadmap Dashboard", layout="wide")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # This reads the file from the SAME folder as the script
    # Ensure your file is named 'data.xlsx' in the repository
    df = pd.read_excel("data.xlsx")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File 'data.xlsx' not found. Please make sure the Excel file is in the same folder as this script.")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

# Department Filter
if 'department' in df.columns:
    dept_options = df['department'].unique().tolist()
    selected_dept = st.sidebar.multiselect("Department", dept_options, default=dept_options)
else:
    selected_dept = []

# Person Filter
if 'person' in df.columns:
    person_options = df['person'].unique().tolist()
    selected_person = st.sidebar.multiselect("Person", person_options, default=person_options)
else:
    selected_person = []

# Apply Filters
# We use simple pandas filtering
df_filtered = df[
    (df['department'].isin(selected_dept)) &
    (df['person'].isin(selected_person))
]

# --- MAIN DASHBOARD ---
st.title("Roadmap Monitoring Dashboard")

# Top Level Metrics
if 'time' in df_filtered.columns:
    total_hours = df_filtered['time'].sum()
    avg_hours = df_filtered['time'].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Projects", len(df_filtered))
    col2.metric("Total Hours", f"{total_hours:.0f}")
    col3.metric("Avg Hours/Project", f"{avg_hours:.1f}")

st.markdown("---")

# --- GRAPHS ---
col_left, col_right = st.columns(2)

# Graph 1: Hours by Person
with col_left:
    if 'person' in df_filtered.columns and 'time' in df_filtered.columns:
        st.subheader("Workload by Person")
        fig_bar = px.bar(
            df_filtered, 
            x='person', 
            y='time', 
            color='department', 
            title="Total Time per Person",
            template="plotly_white"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# Graph 2: Project Timeline (Gantt)
with col_right:
    # Ensure date columns are actual datetime objects
    if 'start date' in df_filtered.columns and 'end date' in df_filtered.columns:
        st.subheader("Project Timeline")
        # Filter out rows with missing dates for the chart
        df_gantt = df_filtered.dropna(subset=['start date', 'end date'])
        
        fig_gantt = px.timeline(
            df_gantt, 
            x_start="start date", 
            x_end="end date", 
            y="person", 
            color="status" if "status" in df_filtered.columns else "department",
            hover_data=["subject"],
            title="Project Schedule"
        )
        # Fix axis to show dates correctly
        fig_gantt.update_yaxes(autorange="reversed") 
        st.plotly_chart(fig_gantt, use_container_width=True)

# --- RAW DATA VIEW ---
with st.expander("View Raw Data"):
    st.dataframe(df_filtered)