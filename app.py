import pandas as pd
import json
import streamlit as st
from io import BytesIO
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder

# Set page configuration 
st.set_page_config(layout="wide", page_title="TMS Trng Insights Dashboard")

# Function to process multiple JSON files
@st.cache_data
def process_json():
    files = [
        "O_CT_DEC_response.JSON", "AUG_OCT_response.JSON",
        "JULY_AUG_response.JSON", "S_JAN25_response.JSON",
        "S_FEB25_response.JSON"
    ]
    sessions, instructors, trainees = [], [], []

    for file in files:
        try:
            with open(file, "r") as uploaded_file:
                data = json.load(uploaded_file)
                for session in data["responseData"]:
                    for ses in session["sessions"]:
                        sessions.append({
                            "sessionId": ses["sessionId"],
                            "date": pd.to_datetime(ses["date"], format="%d/%m/%Y", errors="coerce"),
                            "trainingCourseCode [Curriculum]": ses["trainingCourseCode"],
                            "componentName [Lesson]": ses["componentName"],
                            "startTime": ses["start Time"],
                            "endTime": ses["endTime"]
                        })
                        for instr in ses["instructors"]:
                            instructors.append({
                                "sessionId": ses["sessionId"],
                                "instructor": f"{instr['name']} ({instr['staffNumber']})",
                                "email_instructor": instr.get("email", "N/A"),
                                "dutyCode_instructor": instr["dutyCode"]
                            })
                        for trainee in ses["trainees"]:
                            trainees.append({
                                "sessionId": ses["sessionId"],
                                "trainee": f"{trainee['name']} ({trainee['staffNumber']})",
                                "email_trainee": trainee.get("email", "N/A"),
                                "dutyCode_trainee": trainee["dutyCode"]
                            })
        except FileNotFoundError:
            st.error(f"File {file} not found.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    return pd.DataFrame(sessions), pd.DataFrame(instructors), pd.DataFrame(trainees)

# Process JSON data
sessions_df, instructors_df, trainees_df = process_json()

# Merge DataFrames
merged_df = sessions_df.merge(instructors_df, on="sessionId", how="left").merge(trainees_df, on="sessionId", how="left")
merged_df = merged_df.sort_values(by="date", ascending=False)

# Top-Level KPIs
st.markdown("GRD/SIM Training Insight DB / Jul 2024-Feb 2025", unsafe_allow_html=True)

# Calculate KPI Metrics
total_curriculums = sessions_df["trainingCourseCode [Curriculum]"].nunique()
total_lessons = sessions_df["componentName [Lesson]"].nunique()
total_trainers = instructors_df["instructor"].nunique()
total_trainees = trainees_df["trainee"].nunique()
top_trainer = instructors_df["instructor"].value_counts().idxmax()
top_trainer_sessions = instructors_df["instructor"].value_counts().max()
top_trainee = trainees_df["trainee"].value_counts().idxmax()
top_trainee_sessions = trainees_df["trainee"].value_counts().max()

# Display KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Curriculums", total_curriculums)
    st.metric("Top Trainer", top_trainer)
with col2:
    st.metric("Total Lessons", total_lessons)
    st.metric("Top Trainer Sessions", top_trainer_sessions)
with col3:
    st.metric("Total Trainers", total_trainers)
    st.metric("Top Trainee", top_trainee)
with col4:
    st.metric("Total Trainees", total_trainees)
    st.metric("Top Trainee Sessions", top_trainee_sessions)

# Filtered by Trainee Duty Codes
st.header("Filtered by Trainee Duty Codes")
selected_duty_codes = st.multiselect(
    "Select Trainee Duty Codes",
    merged_df["dutyCode_trainee"].dropna().unique(),
    help="Filter results based on trainee duty codes."
)

# Additional Filters
curriculum_filter = st.multiselect(
    "Select Curriculum",
    merged_df["trainingCourseCode [Curriculum]"].dropna().unique(),
    help="Filter results based on curriculum."
)

lesson_filter = st.multiselect(
    "Select Lesson",
    merged_df["componentName [Lesson]"].dropna().unique(),
    help="Filter results based on lesson."
)

instructor_filter = st.multiselect(
    "Select Instructor",
    merged_df["instructor"].dropna().unique(),
    help="Filter results based on instructor."
)

trainee_filter = st.multiselect(
    "Select Trainee",
    merged_df["trainee"].dropna().unique(),
    help="Filter results based on trainee."
)

start_date = st.date_input("Start Date", value=merged_df["date"].min())
end_date = st.date_input("End Date", value=merged_df["date"].max())
search_text = st.text_input("Search", placeholder="Search across all columns...")

# Apply filters
filtered_df = merged_df.copy()
if selected_duty_codes:
    filtered_df = filtered_df[filtered_df["dutyCode_trainee"].isin(selected_duty_codes)]
if curriculum_filter:
    filtered_df = filtered_df[filtered_df["trainingCourseCode [Curriculum]"].isin(curriculum_filter)]
if lesson_filter:
    filtered_df = filtered_df[filtered_df["componentName [Lesson]"].isin(lesson_filter)]
if instructor_filter:
    filtered_df = filtered_df[filtered_df["instructor"].isin(instructor_filter)]
if trainee_filter:
    filtered_df = filtered_df[filtered_df["trainee"].isin(trainee_filter)]
filtered_df = filtered_df[(filtered_df["date"] >= pd.Timestamp(start_date)) & (filtered_df["date"] <= pd.Timestamp(end_date))]

# Search functionality
if search_text:
    filtered_df = filtered_df[filtered_df.astype(str).apply(lambda row: row.str.contains(search_text, case=False)).any(axis=1)]

# Display filtered DataFrame
st.subheader("Filtered Data")
gb = GridOptionsBuilder.from_dataframe(filtered_df)
gb.configure_pagination(paginationAutoPageSize=True)  # Add pagination
gb.configure_side_bar()  # Add a sidebar
gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum", editable=True)
gridOptions = gb.build()
AgGrid(filtered_df, gridOptions=gridOptions, enable_enterprise_modules=True, height=300, fit_columns_on_grid_load=True)

# Visualizations
st.subheader("Visualizations")
fig = px.bar(filtered_df, x="trainingCourseCode [Curriculum]", y="sessionId", color="instructor", title="Sessions by Curriculum and Instructor")
st.plotly_chart(fig)

fig = px.pie(filtered_df, names="dutyCode_trainee", title="Trainee Duty Codes Distribution")
st.plotly_chart(fig)

# Export Options
st.subheader("Export Data")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download CSV",
    data=csv,
    file_name='filtered_data.csv',
    mime='text/csv'
)

excel = BytesIO()
filtered_df.to_excel(excel, index=False)
st.download_button(
    label="Download Excel",
    data=excel.getvalue(),
    file_name='filtered_data.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)