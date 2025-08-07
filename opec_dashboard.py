import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ------------------------------
# Define OPEC+ countries and series IDs
# ------------------------------
OPEC_SERIES = {
    'Algeria': 'COPR_AG',
    'Congo': 'COPR_CF',
    'Equatorial Guinea': 'COPR_EK',
    'Gabon': 'COPR_GB',
    'Iran': 'COPR_IR',
    'Iraq': 'COPR_IZ',
    'Kuwait': 'COPR_KU',
    'Libya': 'COPR_LY',
    'Nigeria': 'COPR_NI',
    'Saudi Arabia': 'COPR_SA',
    'UAE': 'COPR_TC',
    'Venezuela': 'COPR_VE'
}

OPEC_PLUS_SERIES = {
    'Azerbaijan': 'COPR_AJ',
    'Bahrain': 'COPR_BA',
    'Brunei': 'COPR_BX',
    'Kazakhstan': 'COPR_KZ',
    'Malaysia': 'COPR_MY',
    'Mexico': 'COPR_MX',
    'Oman': 'COPR_MU',
    'Russia': 'COPR_RS',
    'Sudan': 'COPR_SU',
    'South Sudan': 'COPR_OD'
}

ALL_SERIES = {**OPEC_SERIES, **OPEC_PLUS_SERIES}

API_KEY = "hEu3sZUgechYgqPGXrhLG8cOpMhLvxQwC2PPLhcl"
BASE_URL = "https://api.eia.gov/v2/steo/data/"

# ------------------------------
# Fetch data from EIA STEO API
# ------------------------------
def fetch_series_data(series_id):
    today = datetime.today()
    end_date = today.strftime("%Y-%m-%d")

    params = {
        "api_key": API_KEY,
        "frequency": "monthly",
        "data[0]": "value",
        "facets[seriesId][]": series_id,
        "start": "2018-01",
        "end": end_date
    }

    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        st.error(f"Failed to fetch data for {series_id}")
        return None

    data = response.json().get("response", {}).get("data", [])
    df = pd.DataFrame(data)
    if df.empty:
        return None

    df["period"] = pd.to_datetime(df["period"])
    df = df[["period", "value"]].sort_values("period")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["MoM"] = df["value"].pct_change() * 100
    df["YoY"] = df["value"].pct_change(12) * 100
    return df

# ------------------------------
# Plot production chart
# ------------------------------
def plot_production(df, country):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["period"], y=df["value"],
        mode='lines+markers',
        name=country,
        line=dict(width=2)
    ))
    fig.update_layout(
        title=f"{country} Monthly Crude Oil Production (kb/d)",
        xaxis_title="Date",
        yaxis_title="Production (kb/d)",
        template="plotly_dark"
    )
    return fig

# ------------------------------
# Plot YoY / MoM chart
# ------------------------------
def plot_growth(df, country, growth_type="YoY"):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["period"], y=df[growth_type],
        name=growth_type,
        marker_color="crimson" if growth_type == "YoY" else "dodgerblue"
    ))
    fig.update_layout(
        title=f"{country} {growth_type} Change in Production (%)",
        xaxis_title="Date",
        yaxis_title="Change (%)",
        template="plotly_dark"
    )
    return fig

# ------------------------------
# Streamlit Dashboard
# ------------------------------
st.set_page_config(layout="wide")
st.title("\U0001F4CA OPEC+ Crude Oil Production Dashboard")
st.markdown("Monthly crude oil production trends and growth analysis by country (2018–2025)")

# Export PDF
def export_analysis_pdf(analysis_text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(analysis_text, styles['Normal']), Spacer(1, 12)]
    doc.build(elements)
    return buffer

tabs = st.tabs(list(ALL_SERIES.keys()))

for i, (country, series_id) in enumerate(ALL_SERIES.items()):
    with tabs[i]:
        with st.spinner(f"Loading {country} data..."):
            df = fetch_series_data(series_id)
            if df is not None:
                st.plotly_chart(plot_production(df, country), use_container_width=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(plot_growth(df, country, "MoM"), use_container_width=True)
                with col2:
                    st.plotly_chart(plot_growth(df, country, "YoY"), use_container_width=True)

                latest_period = df['period'].max()
                latest_value = df[df['period'] == latest_period]['value'].values[0]
                mom = df[df['period'] == latest_period]['MoM'].values[0]
                yoy = df[df['period'] == latest_period]['YoY'].values[0]
                month_label = latest_period.strftime("%b %Y")

                analysis = (
                    f"As of {month_label}, {country} produced {latest_value:,.0f} kb/d. "
                    f"This represents a {'rise' if yoy > 0 else 'decline'} of {abs(yoy):.1f}% YoY and "
                    f"an {'increase' if mom > 0 else 'drop'} of {abs(mom):.1f}% MoM."
                )
                st.markdown(f"### Analysis\n{analysis}")

                # Export as PDF
                if st.button(f"Export {country} Report as PDF", key=country):
                    pdf = export_analysis_pdf(analysis)
                    st.download_button("📄 Download PDF", data=pdf, file_name=f"{country}_report.pdf", mime="application/pdf")
            else:
                st.warning(f"No data available for {country}")
