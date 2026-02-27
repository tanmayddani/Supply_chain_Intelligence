# dashboards/app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Supply Chain Intelligence Hub",
    layout="wide"
)

# ---------------- PREMIUM UI ----------------
st.markdown("""
<style>

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #eef7f0, #c8e6c9);
}

[data-testid="stSidebar"] {
    display: none;
}

[data-testid="stMetric"] {
    background: white;
    padding: 14px;
    border-radius: 14px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
}

.main-title {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    color: #1b5e20;
    margin-top: 40px; 
    margin-bottom: 15px;
}

.section-header {
    font-size: 18px;
    font-weight: 700;
    color: #1b5e20;
    margin-top: 10px;
    margin-bottom: 6px;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Supply Chain Intelligence Hub</div>', unsafe_allow_html=True)

# ---------------- BIGQUERY CONNECTION ----------------
service_account_path = os.path.join(
    os.path.dirname(__file__),
    '..',
    'supplychainproject-488405-8a4c2bc950ca.json'
)

credentials = service_account.Credentials.from_service_account_file(
    service_account_path
)

client = bigquery.Client(
    credentials=credentials,
    project=credentials.project_id
)

@st.cache_data
def load_data():
    fact_orders = client.query("""
        SELECT * FROM `supplychainproject-488405.supply_chain.fact_orders`
    """).to_dataframe()

    return fact_orders

fact_orders = load_data()
df = fact_orders.copy()

# ---------------- DATE FILTER ----------------
df['order_date'] = pd.to_datetime(df['order_date'])
min_date = df['order_date'].min()
max_date = df['order_date'].max()

date_range = st.date_input("", [min_date, max_date])

if len(date_range) == 2:
    df = df[
        (df['order_date'] >= pd.to_datetime(date_range[0])) &
        (df['order_date'] <= pd.to_datetime(date_range[1]))
    ]

# ---------------- KPI ROW ----------------
total_orders = len(df)
total_revenue = df['sales'].sum()
avg_order_value = df['sales'].mean()
unique_customers = df['customer_name'].nunique()

# Create columns for KPIs + Sales Trends selectors
k1, k2, k3, k4, g_col1, g_col2 = st.columns([1,1,1,1,1,1])

k1.metric("Orders", total_orders)
k2.metric("Revenue", f"${total_revenue:,.0f}")
k3.metric("Avg Order", f"${avg_order_value:,.0f}")
k4.metric("Customers", unique_customers)

# ---------------- Sales Trends selectors (horizontal in same row) ----------------
with g_col1:
    granularity = st.selectbox(
        "Time Granularity",
        ["Monthly", "Daily", "Yearly"],
        key="granularity"
    )

with g_col2:
    metric = st.selectbox(
        "Metric",
        ["Revenue", "Orders", "Average Order Value"],
        key="metric"
    )

# =====================================================
# MAIN GRID (ONE WINDOW)
# =====================================================

col1, col2, col3 = st.columns(3)

# ================= SALES TREND =================
with col1:
    st.markdown('<div class="section-header">📊 Sales Trends</div>', unsafe_allow_html=True)

    if granularity == "Monthly":
        grouped = df.groupby(df['order_date'].dt.to_period("M"))
    elif granularity == "Daily":
        grouped = df.groupby(df['order_date'].dt.date)
    else:
        grouped = df.groupby(df['order_date'].dt.year)

    trend = grouped.agg({
        "sales": ["sum", "mean"],
        "order_id": "count"
    }).reset_index()

    trend.columns = ["date", "revenue", "avg_order_value", "orders"]

    if granularity == "Monthly":
        trend["date"] = pd.to_datetime(trend["date"].astype(str))

    y_col = {
        "Revenue": "revenue",
        "Orders": "orders",
        "Average Order Value": "avg_order_value"
    }[metric]

    fig_trend = px.line(trend, x="date", y=y_col, template="simple_white")
    fig_trend.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))

    st.plotly_chart(fig_trend, use_container_width=True)

# ================= TOP STATES =================
with col2:
    st.markdown('<div class="section-header">🌍 Top States</div>', unsafe_allow_html=True)

    state_sales = (
        df.groupby("state")["sales"]
        .sum()
        .reset_index()
        .sort_values(by="sales", ascending=False)
        .head(7)
    )

    fig_state = px.bar(
        state_sales,
        x="sales",
        y="state",
        orientation="h",
        template="simple_white"
    )
    fig_state.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_state, use_container_width=True)

# ================= ORDER CATEGORY =================
with col3:
    st.markdown('<div class="section-header">📦 Order Category</div>', unsafe_allow_html=True)

    df["Order Type"] = pd.cut(
        df["sales"],
        bins=[0, 200, 800, df["sales"].max()],
        labels=["Small", "Mid", "High"]
    )

    order_type_data = (
        df.groupby("Order Type")["order_id"]
        .count()
        .reset_index()
    )

    fig_order = px.bar(
        order_type_data,
        x="Order Type",
        y="order_id",
        template="simple_white"
    )
    fig_order.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_order, use_container_width=True)

# ================= BOTTOM ROW =================
b1, b2 = st.columns(2)

with b1:
    st.markdown('<div class="section-header">📈 Revenue Share</div>', unsafe_allow_html=True)

    fig_pie = px.pie(
        state_sales.head(5),
        values="sales",
        names="state",
        hole=0.5,
        template="simple_white"
    )
    fig_pie.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_pie, use_container_width=True)

with b2:
    st.markdown('<div class="section-header">🏆 Top Customers</div>', unsafe_allow_html=True)

    customer_orders = (
        df.groupby("customer_name")["order_id"]
        .count()
        .reset_index()
        .sort_values(by="order_id", ascending=False)
        .head(7)
    )

    fig_freq = px.bar(
        customer_orders,
        x="order_id",
        y="customer_name",
        orientation="h",
        template="simple_white"
    )
    fig_freq.update_layout(
        yaxis=dict(autorange="reversed"),
        height=250,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(fig_freq, use_container_width=True)