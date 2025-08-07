import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

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
                      xaxis_title="Period", yaxis_title="Production (kb/d)", height=300)
    return fig

# --- Analysis (YoY Change) ---
def generate_analysis(df):
    if df.empty:
        return "No data available for analysis."

    df = df.sort_values("period")
    latest_row = df.iloc[-1]
    latest_period = latest_row["period"]
    latest_value = float(latest_row["value"])

    year_ago_date = latest_period - pd.DateOffset(years=1)
    year_ago_row = df[df["period"] == year_ago_date]

    if year_ago_row.empty:
        return "Insufficient historical data for YoY comparison."

    year_ago_value = float(year_ago_row.iloc[0]["value"])
    change = latest_value - year_ago_value
    pct_change = (change / year_ago_value) * 100

    return f"{latest_period.strftime('%b %Y')}: {latest_value:.2f} mb/d ({pct_change:+.1f}% YoY)"

# --- Export to PDF using Matplotlib ---
def export_all_countries_pdf(data_dict, title_prefix="OPEC & OPEC+ Crude Oil Production", filename="opec_production_report.pdf"):
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mtick
    from matplotlib.backends.backend_pdf import PdfPages
    import pandas as pd

    countries = list(data_dict.keys())
    n_cols = 3
    n_rows = (len(countries) + n_cols - 1) // n_cols
    fig, axs = plt.subplots(n_rows, n_cols, figsize=(15, n_rows * 3), constrained_layout=True)

    # Flatten axs for easier access
    axs = axs.flatten() if n_rows > 1 else axs

    for idx, (country, df) in enumerate(data_dict.items()):
        ax = axs[idx]

        # Ensure correct date and value order
        df_sorted = df.sort_values('period')
        dates = pd.to_datetime(df_sorted['period'])
        values = df_sorted['value']

        ax.plot(dates, values, label=country, color='blue')
        ax.set_title(f"{title_prefix}: {country}", fontsize=9)
        ax.set_xlabel("Date", fontsize=7)
        ax.set_ylabel("Production (mb/d)", fontsize=7)

        # Format y-axis
        ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=4, prune='both'))
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x:.1f}'))
        ax.grid(True, linewidth=0.3)
        ax.tick_params(axis='x', labelrotation=30, labelsize=6)
        ax.tick_params(axis='y', labelsize=6)

    # Hide unused subplots
    for idx in range(len(data_dict), len(axs)):
        axs[idx].axis("off")

    # Save to PDF
    with PdfPages(filename) as pdf:
        pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
    return filename

    
# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("OPEC & OPEC+ Crude Oil Production Dashboard")

selected_countries = st.multiselect("Select countries/regions to display", options=list(SERIES_IDS.values()), default=list(SERIES_IDS.values()))
data_dict = {}

cols_per_row = 3

country_names = []
country_dfs = []

for name in selected_countries:
    series_id = [k for k, v in SERIES_IDS.items() if v == name][0]
    with st.spinner(f"Fetching data for {name}..."):
        df = fetch_series_data(series_id)
        if not df.empty:
            data_dict[name] = df
            country_names.append(name)
            country_dfs.append(df)

# Render plots in grid layout
for i in range(0, len(country_names), cols_per_row):
    cols = st.columns(cols_per_row)
    for j in range(cols_per_row):
        if i + j < len(country_names):
            name = country_names[i + j]
            df = country_dfs[i + j]
            with cols[j]:
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


