import streamlit as st
import pandas as pd

st.title("Concession Dashboard")

uploaded_file = st.file_uploader(
    "Upload Concession Excel File",
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # Find disposition column
    disposition_col = "Disposition Decision"

    # Count dispositions
    race_ready = df[disposition_col].astype(str).str.contains(
        "Race Ready",
        case=False,
        na=False
    ).sum()

    development = df[disposition_col].astype(str).str.contains(
        "Development",
        case=False,
        na=False
    ).sum()

    scrap = df[disposition_col].astype(str).str.contains(
        "Scrap",
        case=False,
        na=False
    ).sum()

    st.subheader("Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("🏁 Race Ready", race_ready)
    col2.metric("🔧 Development", development)
    col3.metric("🗑️ Scrap", scrap)

    summary = pd.DataFrame({
        "Category": ["Race Ready", "Development", "Scrap"],
        "Count": [race_ready, development, scrap]
    })

    st.bar_chart(
        summary.set_index("Category")
    )

    st.subheader("Raw Data")
    st.dataframe(df)
