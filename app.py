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
        "S_01-15_DEC24_response.JSON", "S_15-31_DEC24_response.JSON",
        "S_01-15_JAN25_response.JSON", "S_15-31_JAN25_response.JSON",
        "S_01-15_FEB25_response.JSON", "S_15-28_FEB25_response.JSON",
        "S_01-15_MAR25_response.JSON", "S_15-31_MAR25_response.JSON",
        "S_01-15_APR25_response.JSON", "S_15-30_APR25_response.JSON",
        "S_01-31_MAY25_response.JSON", "S_01-30_JUN25_response.JSON",
        "S_28MAY25_31JUL25_response.JSON"
    ]
    sessions, instructors, trainees = [], [], []

    for file in files:
        try:
            with open(file, "r") as uploaded_file:
                data = json.load(uploaded_file)
                for session in data["responseData"]:
                    for ses in session["sessions"]:
                        sessions.append({
                            "sessionId":
                            ses["sessionId"],
                            "date":
                            pd.to_datetime(ses["date"],
                                           format="%d/%m/%Y",
                                           errors="coerce"),
                            "trainingCourseCode [Curriculum]":
                            ses["trainingCourseCode"],
                            "componentName [Lesson]":
                            ses["componentName"],
                            "startTime":
                            ses["startTime"],
                            "endTime":
                            ses["endTime"]
                        })
                        for instr in ses["instructors"]:
                            instructors.append({
                                "sessionId":
                                ses["sessionId"],
                                "instructor":
                                f"{instr['name']} ({instr['staffNumber']})",
                                "email_instructor":
                                instr.get("email", "N/A"),
                                "dutyCode_instructor":
                                instr["dutyCode"]
                            })
                        for trainee in ses["trainee"]:
                            trainees.append({
                                "sessionId":
                                ses["sessionId"],
                                "trainee":
                                f"{trainee['name']} ({trainee['staffNumber']})",
                                "email_trainee":
                                trainee.get("email", "N/A"),
                                "dutyCode_trainee":
                                trainee["dutyCode"]
                            })
        except FileNotFoundError:
            st.error(f"File {file} not found.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    return pd.DataFrame(sessions), pd.DataFrame(instructors), pd.DataFrame(
        trainees)


# Process JSON data
sessions_df, instructors_df, trainees_df = process_json()

# Merge DataFrames
merged_df = sessions_df.merge(instructors_df, on="sessionId",
                              how="left").merge(trainees_df,
                                                on="sessionId",
                                                how="left")
merged_df = merged_df.sort_values(by="date", ascending=False)

# Top-Level KPIs
st.markdown(
    "<h1 style='text-align: center;'>GRD/SIM Training Insight DB / Dec 2024 - Jul 2025</h1>",
    unsafe_allow_html=True)

# CSS for enhanced styling
st.markdown("""
    <style>
        .flex-container {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            align-items: center;
        }
        .filter-item {
            flex: 1;
            min-width: 200px;
        }
        .kpi-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 10px;
            margin: 5px;
            font-size: 14px;
        }
        .kpi-header {
            font-weight: bold;
            font-size: 16px;
        }
    </style>
    """,
            unsafe_allow_html=True)

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
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Total Curriculums</div>{total_curriculums}</div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Top Trainer</div>{top_trainer}</div>",
        unsafe_allow_html=True)
with col2:
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Total Lessons</div>{total_lessons}</div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Top Trainer Sessions</div>{top_trainer_sessions}</div>",
        unsafe_allow_html=True)
with col3:
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Total Trainers</div>{total_trainers}</div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Top Trainee</div>{top_trainee}</div>",
        unsafe_allow_html=True)
with col4:
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Total Trainees</div>{total_trainees}</div>",
        unsafe_allow_html=True)
    st.markdown(
        f"<div class='kpi-box'><div class='kpi-header'>Top Trainee Sessions</div>{top_trainee_sessions}</div>",
        unsafe_allow_html=True)

# Filtered by Trainee Duty Codes
st.header("Filtered by Trainee Duty Codes")
selected_duty_codes = st.multiselect(
    "Select Trainee Duty Codes",
    merged_df["dutyCode_trainee"].dropna().unique(),
    help="Filter results based on trainee duty codes.")

if selected_duty_codes:
    duty_filtered_df = merged_df[merged_df["dutyCode_trainee"].isin(
        selected_duty_codes)]

    st.markdown("<div class='flex-container'>", unsafe_allow_html=True)
    start_date = st.date_input("Start Date",
                               value=duty_filtered_df["date"].min())
    end_date = st.date_input("End Date", value=duty_filtered_df["date"].max())
    search_text = st.text_input("Search",
                                placeholder="Search across all columns...")
    st.markdown("</div>", unsafe_allow_html=True)

    # Apply filters
    duty_filtered_df = duty_filtered_df[
        (duty_filtered_df["date"] >= pd.Timestamp(start_date))
        & (duty_filtered_df["date"] <= pd.Timestamp(end_date))]
    if search_text:
        duty_filtered_df = duty_filtered_df[duty_filtered_df.apply(
            lambda row: row.astype(str).str.contains(search_text, case=False
                                                     ).any(),
            axis=1)]

    st.subheader("Filtered Results by Duty Codes")
    display_columns = [
        col for col in duty_filtered_df.columns if col != "sessionId"
    ]
    gb = GridOptionsBuilder.from_dataframe(duty_filtered_df[display_columns])
    gb.configure_default_column(sortable=True, filterable=True, resizable=True)
    AgGrid(duty_filtered_df[display_columns],
           gridOptions=gb.build(),
           height=300,
           theme="streamlit")

    st.subheader("Lesson Distribution by Duty Codes")
    insights_chart = duty_filtered_df.groupby(
        ["trainingCourseCode [Curriculum]",
         "componentName [Lesson]"]).size().reset_index(name="Count")
    fig = px.bar(insights_chart,
                 x="trainingCourseCode [Curriculum]",
                 y="Count",
                 color="componentName [Lesson]",
                 title="Lesson Distribution")
    st.plotly_chart(fig, use_container_width=True)

# Curriculum and Lesson Insights
st.header("Curriculum and Lesson Insights")
selected_courses = st.multiselect(
    "Select Curriculums (Training Course Codes)",
    merged_df["trainingCourseCode [Curriculum]"].dropna().unique(),
    help="Choose a curriculum to view its lessons.")

if selected_courses:
    filtered_df = merged_df[merged_df["trainingCourseCode [Curriculum]"].isin(
        selected_courses)]
    lessons = filtered_df["componentName [Lesson]"].dropna().unique().tolist()
    select_all = st.checkbox("Select All Lessons", value=False)
    selected_components = lessons if select_all else st.multiselect(
        "Select Lessons (Component Names)", lessons)

    if selected_components:
        final_filtered_df = filtered_df[
            filtered_df["componentName [Lesson]"].isin(selected_components)]

        st.markdown("<div class='flex-container'>", unsafe_allow_html=True)
        start_date = st.date_input("Start Date",
                                   value=final_filtered_df["date"].min(),
                                   key="lesson_start_date")
        end_date = st.date_input("End Date",
                                 value=final_filtered_df["date"].max(),
                                 key="lesson_end_date")
        search_text = st.text_input("Search",
                                    placeholder="Search across all columns...",
                                    key="lesson_search_text")
        st.markdown("</div>", unsafe_allow_html=True)

        # Apply filters
        final_filtered_df = final_filtered_df[
            (final_filtered_df["date"] >= pd.Timestamp(start_date))
            & (final_filtered_df["date"] <= pd.Timestamp(end_date))]
        if search_text:
            final_filtered_df = final_filtered_df[final_filtered_df.apply(
                lambda row: row.astype(str).str.contains(search_text,
                                                         case=False).any(),
                axis=1)]

        st.subheader("Filtered Results by Curriculum and Lesson")
        display_columns = [
            col for col in final_filtered_df.columns if col != "sessionId"
        ]
        gb = GridOptionsBuilder.from_dataframe(
            final_filtered_df[display_columns])
        gb.configure_default_column(sortable=True,
                                    filterable=True,
                                    resizable=True)
        AgGrid(final_filtered_df[display_columns],
               gridOptions=gb.build(),
               height=300,
               theme="streamlit")

        # Visualization
        st.subheader("Lesson Distribution by Curriculum Names")
        distribution_chart = final_filtered_df.groupby(
            ["trainingCourseCode [Curriculum]",
             "componentName [Lesson]"]).size().reset_index(name="Count")
        distribution_fig = px.treemap(
            distribution_chart,
            path=["trainingCourseCode [Curriculum]", "componentName [Lesson]"],
            values="Count",
            title="Lesson Distribution by Curriculum")
        st.plotly_chart(distribution_fig, use_container_width=True)

        # Download filtered data
        st.subheader("Download Filtered Data")
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            final_filtered_df.to_excel(writer,
                                       index=False,
                                       sheet_name="Filtered Data")
        st.download_button(
            label="Download Filtered Results",
            data=buffer.getvalue(),
            file_name="filtered_results.xlsx",
            mime=
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
