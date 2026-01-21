import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Roadmap Dashboard", layout="wide")

# --- GROUP MAPPING ---
GROUP_MAPPING = {
    0: "0 - Formalize a Roadmap (Soft skills)",
    1: "1 - Develop Internal Capacity (Contribution to LISER)",
    2: "2 - Advise Data Science Solutions (Technical Excellence)",
    3: "3 - Publish Research in AI (Scientific Excellence)",
    4: "4 - Foster Strategic Collaborations (Societal Impact)"
}

# --- LOAD DATA ---
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'Roadmap_Monitoring_System_2.xlsx')
    
    try:
        # 1. Load the file
        df = pd.read_excel(file_path)
        
        # 2. Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # 3. FIX: Map empty cells (NaN) in 'status' to 'Ongoing'
        # We do this BEFORE converting to text to catch the real empty cells
        if 'status' in df.columns:
            df['status'] = df['status'].fillna('Ongoing')

        # 4. Clean textual columns (stripping whitespace)
        # This ensures "Ongoing " and "Ongoing" are treated as the same
        text_cols = ['status', 'department', 'person', 'subject', 'comment']
        for col in text_cols:
            if col in df.columns:
                # Convert to string and strip spaces
                df[col] = df[col].astype(str).str.strip()
                # Extra safety: if an empty cell somehow became the text "nan", fix it here
                if col == 'status':
                    df[col] = df[col].replace('nan', 'Ongoing')

        # 5. Convert date columns
        date_cols = ['start date', 'end date', 'start_date', 'end_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

        # 6. Pre-process 'group' column for filtering
        if 'group' in df.columns:
            df['group_list'] = df['group'].astype(str).str.split(';').apply(
                lambda x: [int(float(i)) for i in x if i.strip().replace('.', '').isdigit()]
            )
        else:
            df['group_list'] = []

        # 7. Extract Year and Month
        start_col = 'start date' if 'start date' in df.columns else 'start_date'
        if start_col in df.columns:
            df['Year'] = df[start_col].dt.year
            df['Month'] = df[start_col].dt.month_name()
            df['month_num'] = df[start_col].dt.month 
        
        return df
    except FileNotFoundError:
        st.error(f"File not found! Looked for: {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Options")

# 1. STATUS FILTER
# Automatically picks up "Finished", "Ongoing", etc.
if 'status' in df.columns:
    status_options = df['status'].unique().tolist()
    # Default to selecting ALL statuses
    selected_status = st.sidebar.multiselect("Select Status", status_options, default=status_options)
else:
    selected_status = []

# 2. YEAR FILTER
if 'Year' in df.columns:
    unique_years = sorted([int(x) for x in df['Year'].dropna().unique()])
    selected_years = st.sidebar.multiselect("Select Year", unique_years, default=unique_years)
else:
    selected_years = []

# 3. MONTH FILTER
if 'Month' in df.columns:
    unique_months = df.sort_values('month_num')['Month'].dropna().unique()
    selected_months = st.sidebar.multiselect("Select Month", unique_months, default=unique_months)
else:
    selected_months = []

# 4. GROUP FILTER (Mapped)
if 'group_list' in df.columns:
    all_ids = set()
    for sublist in df['group_list']:
        all_ids.update(sublist)
    
    group_options = [GROUP_MAPPING.get(gid, f"Group {gid}") for gid in sorted(all_ids)]
    selected_group_names = st.sidebar.multiselect("Select Group", group_options, default=group_options)
    
    selected_group_ids = []
    for name in selected_group_names:
        for gid, gname in GROUP_MAPPING.items():
            if gname == name:
                selected_group_ids.append(gid)
        if "Group " in name:
            try:
                selected_group_ids.append(int(name.replace("Group ", "")))
            except:
                pass
else:
    selected_group_ids = []

# 5. DEPARTMENT & PERSON FILTERS
if 'department' in df.columns:
    dept_options = df['department'].unique().tolist()
    selected_dept = st.sidebar.multiselect("Department", dept_options, default=dept_options)
else:
    selected_dept = []

if 'person' in df.columns:
    person_options = df['person'].unique().tolist()
    selected_person = st.sidebar.multiselect("Person", person_options, default=person_options)
else:
    selected_person = []

# --- APPLY FILTERS ---
df_filtered = df.copy()

if 'status' in df.columns and selected_status:
    df_filtered = df_filtered[df_filtered['status'].isin(selected_status)]

if 'Year' in df.columns and selected_years:
    df_filtered = df_filtered[df_filtered['Year'].isin(selected_years)]

if 'Month' in df.columns and selected_months:
    df_filtered = df_filtered[df_filtered['Month'].isin(selected_months)]

if 'department' in df.columns and selected_dept:
    df_filtered = df_filtered[df_filtered['department'].isin(selected_dept)]

if 'person' in df.columns and selected_person:
    df_filtered = df_filtered[df_filtered['person'].isin(selected_person)]

if 'group_list' in df.columns and selected_group_ids:
    def has_overlap(row_groups):
        return any(gid in selected_group_ids for gid in row_groups)
    df_filtered = df_filtered[df_filtered['group_list'].apply(has_overlap)]


# --- MAIN DASHBOARD ---
st.title("Roadmap Monitoring Dashboard")

# Metrics
if 'time' in df_filtered.columns:
    total_hours = df_filtered['time'].sum()
    avg_hours = df_filtered['time'].mean() if not df_filtered.empty else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Projects", len(df_filtered))
    col2.metric("Total Hours", f"{total_hours:.0f}")
    col3.metric("Avg Hours/Project", f"{avg_hours:.1f}")

st.markdown("---")

# --- GRAPHS (Row 1) ---
col_left, col_right = st.columns(2)

# Graph 1: Workload by DEPARTMENT
with col_left:
    if 'department' in df_filtered.columns and 'time' in df_filtered.columns:
        st.subheader("Workload by Department")
        df_dept = df_filtered.groupby('department')['time'].sum().reset_index()
        
        fig_dept = px.bar(
            df_dept, 
            x='department', 
            y='time', 
            color='department',
            title="Total Time per Department",
            template="plotly_white",
            text_auto=True
        )
        st.plotly_chart(fig_dept, use_container_width=True)

# Graph 2: Project Timeline by SUBJECT (With Comments on Hover)
with col_right:
    start_col = 'start date' if 'start date' in df_filtered.columns else 'start_date'
    end_col = 'end date' if 'end date' in df_filtered.columns else 'end_date'
    
    if start_col in df_filtered.columns and end_col in df_filtered.columns and 'subject' in df_filtered.columns:
        st.subheader("Project Schedule (By Subject)")
        df_gantt = df_filtered.dropna(subset=[start_col, end_col])
        
        # Prepare hover data
        hover_items = ["person", "status"]
        if "comment" in df_filtered.columns:
            hover_items.append("comment")

        if not df_gantt.empty:
            fig_gantt = px.timeline(
                df_gantt, 
                x_start=start_col, 
                x_end=end_col, 
                y="subject", 
                color="status" if "status" in df_filtered.columns else "department",
                hover_data=hover_items,
                title="Timeline by Subject (Hover bar for comments)"
            )
            fig_gantt.update_yaxes(autorange="reversed") 
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            st.info("No dates available for this selection.")

# --- GRAPHS (Row 2 - Full Width) ---
st.markdown("---")

# Graph 3: Workload by PERSON (Sorted High -> Low)
if 'person' in df_filtered.columns and 'time' in df_filtered.columns:
    st.subheader("Workload Leaderboard (Person)")
    # Group and sum
    df_person = df_filtered.groupby(['person', 'department'])['time'].sum().reset_index()
    # Sort descending
    df_person = df_person.sort_values(by='time', ascending=False)
    
    fig_person = px.bar(
        df_person, 
        x='person', 
        y='time', 
        color='department', 
        title="Total Time per Person (Highest to Lowest)",
        template="plotly_white",
        text_auto=True
    )
    fig_person.update_layout(xaxis={'categoryorder':'total descending'})
    
    st.plotly_chart(fig_person, use_container_width=True)

# --- RAW DATA VIEW ---
with st.expander("View Raw Data"):
    st.dataframe(df_filtered)