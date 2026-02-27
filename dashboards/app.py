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

/* Hide Sidebar */
[data-testid="stSidebar"] {
    display: none;
}

/* KPI Cards */
[data-testid="stMetric"] {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 6px 25px rgba(0,0,0,0.08);
}

/* Main Title */
.main-title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    color: #1b5e20;
    margin-bottom: 50px;
    letter-spacing: 1px;
}

/* Section Titles */
.section-header {
    text-align: center;
    font-size: 32px;
    font-weight: 700;
    color: #2e7d32;
    margin-top: 80px;
    margin-bottom: 40px;
}

/* Chart Titles */
.chart-title {
    text-align: center;
    font-size: 20px;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 15px;
    color: #1b5e20;
}

/* Better spacing */
.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
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

    dim_customers = client.query("""
        SELECT * FROM `supplychainproject-488405.supply_chain.dim_customer`
    """).to_dataframe()

    dim_people = client.query("""
        SELECT * FROM `supplychainproject-488405.supply_chain.dim_people`
    """).to_dataframe()

    return fact_orders, dim_customers, dim_people


fact_orders, dim_customers, dim_people = load_data()
df = fact_orders.copy()

# ---------------- DATE FILTER ----------------
df['order_date'] = pd.to_datetime(df['order_date'])

min_date = df['order_date'].min()
max_date = df['order_date'].max()

date_range = st.date_input("Select Date Range", [min_date, max_date])

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

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Orders", total_orders)
k2.metric("Total Revenue", f"${total_revenue:,.0f}")
k3.metric("Average Order Value", f"${avg_order_value:,.0f}")
k4.metric("Unique Customers", unique_customers)

# =====================================================
# SALES TRENDS
# =====================================================

st.markdown('<div class="section-header">Sales Trends</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
granularity = c1.selectbox("Time Granularity", ["Monthly", "Daily", "Yearly"])
metric = c2.selectbox("Metric", ["Revenue", "Orders", "Average Order Value"])

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

st.markdown('<div class="chart-title">Performance Trend</div>', unsafe_allow_html=True)

fig_trend = px.line(
    trend,
    x="date",
    y=y_col,
    template="simple_white",
    color_discrete_sequence=["#2e7d32"]
)

fig_trend.update_layout(
    margin=dict(l=80, r=80, t=40, b=60),
    height=500
)

st.plotly_chart(fig_trend, use_container_width=True)

trend["moving_avg"] = trend[y_col].rolling(3).mean()

st.markdown('<div class="chart-title">3-Period Moving Average</div>', unsafe_allow_html=True)

fig_ma = px.line(
    trend,
    x="date",
    y="moving_avg",
    template="simple_white",
    color_discrete_sequence=["#1b5e20"]
)

fig_ma.update_layout(
    margin=dict(l=80, r=80, t=40, b=60),
    height=450
)

st.plotly_chart(fig_ma, use_container_width=True)

# =====================================================
# GEOGRAPHIC INSIGHTS
# =====================================================

st.markdown('<div class="section-header">Geographic Insights</div>', unsafe_allow_html=True)

state_sales = (
    df.groupby("state")["sales"]
    .sum()
    .reset_index()
    .sort_values(by="sales", ascending=False)
)

g1, g2 = st.columns(2)

with g1:
    st.markdown('<div class="chart-title">Top 10 States by Revenue</div>', unsafe_allow_html=True)
    fig_state = px.bar(
        state_sales.head(10),
        x="sales",
        y="state",
        orientation="h",
        template="simple_white",
        color="sales",
        color_continuous_scale=["#c8e6c9", "#1b5e20"]
    )
    fig_state.update_layout(margin=dict(l=80, r=40, t=30, b=60), height=500)
    st.plotly_chart(fig_state, use_container_width=True)

with g2:
    st.markdown('<div class="chart-title">Revenue Share (Top 5 States)</div>', unsafe_allow_html=True)
    fig_pie = px.pie(
        state_sales.head(5),
        values="sales",
        names="state",
        hole=0.55,
        template="simple_white"
    )
    fig_pie.update_layout(margin=dict(l=40, r=80, t=30, b=60), height=500)
    st.plotly_chart(fig_pie, use_container_width=True)

# =====================================================
# ORDER INSIGHTS
# =====================================================

st.markdown('<div class="section-header">Order Insights</div>', unsafe_allow_html=True)

o1, o2 = st.columns(2)

with o1:
    st.markdown('<div class="chart-title">Order Type Distribution</div>', unsafe_allow_html=True)

    # Create Order Type Categories
    df["Order Type"] = pd.cut(
        df["sales"],
        bins=[0, 200, 800, df["sales"].max()],
        labels=["Small Orders", "Mid-Range Orders", "High-Value Orders"]
    )

    order_type_data = (
        df.groupby("Order Type")["order_id"]
        .count()
        .reset_index()
    )

    fig_order_type = px.bar(
        order_type_data,
        x="Order Type",
        y="order_id",
        template="simple_white",
        color="Order Type",
        color_discrete_sequence=["#a5d6a7", "#66bb6a", "#1b5e20"]
    )

    fig_order_type.update_layout(
        xaxis_title="Order Category",
        yaxis_title="Number of Orders",
        margin=dict(l=80, r=40, t=30, b=60),
        height=500
    )

    st.plotly_chart(fig_order_type, use_container_width=True)

with o2:
    st.markdown('<div class="chart-title">Top Customers by Order Frequency</div>', unsafe_allow_html=True)
    customer_orders = (
        df.groupby("customer_name")["order_id"]
        .count()
        .reset_index()
        .sort_values(by="order_id", ascending=False)
        .head(10)
    )
    fig_freq = px.bar(
        customer_orders,
        x="order_id",
        y="customer_name",
        orientation="h",
        template="simple_white",
        color="order_id",
        color_continuous_scale=["#a5d6a7", "#1b5e20"]
    )
    fig_freq.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=80, r=40, t=30, b=60),
        height=500
    )
    st.plotly_chart(fig_freq, use_container_width=True)