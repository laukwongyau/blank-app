import streamlit as st
import pandas as pd
import requests
from requests_ntlm import HttpNtlmAuth

try:
    from requests_negotiate_sspi import HttpNegotiateAuth
    HAS_SSPI = True
except ImportError:
    HAS_SSPI = False

SITE_URL = "http://intranet/sites/rbpt-qrs"
LIST_TITLE = "Concession Request System"

st.title("Concession Dashboard")


def get_sharepoint_credentials():
    if HAS_SSPI:
        return None

    st.sidebar.subheader("SharePoint credentials")
    username = st.sidebar.text_input("Domain\\Username")
    password = st.sidebar.text_input("Password", type="password")
    return (username, password)


@st.cache_data(ttl=300, show_spinner="Pulling concession data from SharePoint...")
def fetch_concession_data(credentials):
    auth = HttpNegotiateAuth() if credentials is None else HttpNtlmAuth(*credentials)
    headers = {"Accept": "application/json;odata=nometadata"}

    url = (
        f"{SITE_URL}/_api/web/lists/getbytitle('{LIST_TITLE}')/items"
        "?$select=FieldValuesAsText/*&$expand=FieldValuesAsText&$top=2000"
    )

    rows = []
    while url:
        response = requests.get(url, auth=auth, headers=headers, timeout=60)
        response.raise_for_status()
        payload = response.json()
        rows.extend(item["FieldValuesAsText"] for item in payload["value"])
        url = payload.get("odata.nextLink") or payload.get("@odata.nextLink")

    return pd.DataFrame(rows)


source = st.radio(
    "Data source",
    ["Pull from Concession System", "Upload Excel File"],
    horizontal=True
)

df = None

if source == "Pull from Concession System":
    credentials = get_sharepoint_credentials()
    if st.button("Load / Refresh data"):
        fetch_concession_data.clear()
    try:
        df = fetch_concession_data(credentials)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the Concession System: {e}")
else:
    uploaded_file = st.file_uploader(
        "Upload Concession Excel File",
        type=["xlsx"]
    )
    if uploaded_file:
        df = pd.read_excel(uploaded_file)

if df is not None:

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

    dates = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce").dt.date.dropna()

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
        row_dates = pd.to_datetime(filtered_df[date_col], dayfirst=True, errors="coerce").dt.date
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
