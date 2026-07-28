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
    part_no_col = "Part No."
    date_col = "Date Raised"

    st.subheader("Filters")

    filter_col1, filter_col2 = st.columns([1, 2])

    with filter_col1:
        part_search = st.text_input(
            "Search Part No.",
            placeholder="e.g. RBPT01-MK-00741"
        )

    dates = pd.to_datetime(df[date_col], errors="coerce").dt.date.dropna()

    with filter_col2:
        if not dates.empty:
            min_date, max_date = dates.min(), dates.max()
            date_range = st.slider(
                "Date Raised range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date)
            )
        else:
            date_range = None

    filtered_df = df

    if part_search:
        filtered_df = filtered_df[
            filtered_df[part_no_col].astype(str).str.contains(
                part_search,
                case=False,
                na=False
            )
        ]

    if date_range:
        row_dates = pd.to_datetime(filtered_df[date_col], errors="coerce").dt.date
        filtered_df = filtered_df[row_dates.between(date_range[0], date_range[1])]

    st.caption(f"Showing {len(filtered_df)} of {len(df)} records")

    # Count dispositions
    race_ready = filtered_df[disposition_col].astype(str).str.contains(
        "Race Ready",
        case=False,
        na=False
    ).sum()

    development = filtered_df[disposition_col].astype(str).str.contains(
        "Development",
        case=False,
        na=False
    ).sum()

    scrap = filtered_df[disposition_col].astype(str).str.contains(
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
    st.dataframe(filtered_df)
