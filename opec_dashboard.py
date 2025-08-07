import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

# --- Constants ---
API_URL = "https://api.eia.gov/v2/steo/data/"
API_KEY = "hEu3sZUgechYgqPGXrhLG8cOpMhLvxQwC2PPLhcl"

# --- Series IDs ---
SERIES_IDS = {
    'COPR_AG': 'Algeria',
    'COPR_CF': 'Congo',
    'COPR_EK': 'Equatorial Guinea',
    'COPR_GB': 'Gabon',
    'COPR_IR': 'Iran',
    'COPR_IZ': 'Iraq',
    'COPR_KU': 'Kuwait',
    'COPR_LY': 'Libya',
    'COPR_NI': 'Nigeria',
    'COPR_SA': 'Saudi Arabia',
    'COPR_TC': 'UAE',
    'COPR_VE': 'Venezuela',
    'COPR_AJ': 'Azerbaijan',
    'COPR_BA': 'Bahrain',
    'COPR_BX': 'Brunei',
    'COPR_KZ': 'Kazakhstan',
    'COPR_MY': 'Malaysia',
    'COPR_MX': 'Mexico',
    'COPR_MU': 'Oman',
    'COPR_RS': 'Russia',
    'COPR_SU': 'Sudan',
    'COPR_OD': 'South Sudan'
}

# --- Fetch and Process Data ---
def fetch_series_data(series_id):
    params = {
        "api_key": API_KEY,
        "frequency": "monthly",
        "data[0]": "value",
        "facets[seriesId][]": series_id,
        "start": "2018-01",
        "end": datetime.today().strftime("%Y-%m")
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        raw = response.json()["response"]["data"]
        df = pd.DataFrame(raw)
        df = df.sort_values("period")
        df["period"] = pd.to_datetime(df["period"])
        return df
    except Exception as e:
        st.error(f"Error fetching data for {series_id}: {e}")
        return pd.DataFrame()

# --- Generate Plotly Chart ---
def plotly_production_chart(df, country):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['period'], y=df['value'], mode='lines+markers', name=country))
    fig.update_layout(title=f"{country} Crude Oil Production",
                      xaxis_title="Period", yaxis_title="Production (kb/d)", height=400)
    return fig

# --- Analysis (YoY Change) ---
def generate_analysis(df):
    if len(df) < 13:
        return "Not enough data for analysis."
    latest = df.iloc[-1]
    year_ago = df[df["period"] == latest["period"] - pd.DateOffset(years=1)]
    if not year_ago.empty:
        change = latest["value"] - year_ago.iloc[0]["value"]
        pct_change = (change / year_ago.iloc[0]["value"]) * 100
        return f"YoY Change: {change:.0f} kb/d ({pct_change:.1f}%)"
    return "YoY comparison unavailable."

# --- Export to PDF using Matplotlib ---
def export_all_countries_pdf(data_dict, title_prefix="OPEC+ Crude Oil Production", filename="opec_production_report.pdf"):
    with PdfPages(filename) as pdf:
        for country, df in data_dict.items():
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(pd.to_datetime(df['period']), df['value'], label=country, color='blue')
            ax.set_title(f"{title_prefix}: {country}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Production (mb/d)")
            ax.grid(True)
            ax.legend()
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)
    return filename

# --- Streamlit UI ---
st.title("OPEC & OPEC+ Crude Oil Production Dashboard")

selected_countries = st.multiselect("Select countries/regions to display", options=list(SERIES_IDS.values()), default=list(SERIES_IDS.values()))
data_dict = {}

for name in selected_countries:
    # Reverse lookup the series_id
    series_id = [k for k, v in SERIES_IDS.items() if v == name][0]
    with st.spinner(f"Fetching data for {name}..."):
        df = fetch_series_data(series_id)
        if not df.empty:
            data_dict[name] = df
            st.plotly_chart(plotly_production_chart(df, name), use_container_width=True)
            st.caption(generate_analysis(df))

# --- PDF Export ---
if st.button("📄 Download PDF Report"):
    with st.spinner("Generating PDF report..."):
        pdf_file = export_all_countries_pdf(data_dict)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📥 Download PDF",
                data=f,
                file_name="OPEC_Production_Report.pdf",
                mime="application/pdf"
            )
