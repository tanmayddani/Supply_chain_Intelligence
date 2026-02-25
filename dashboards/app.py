# dashboards/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Supply Chain Intelligence Hub",
    layout="wide",
    page_icon="🚀"
)

# ---------------- MODERN CSS ----------------
st.markdown("""
<style>

/* Background */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f1f8e9, #c5e1a5);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0d3b2e;
}
[data-testid="stSidebar"] * {
    color: white !important;
}

/* KPI Cards */
[data-testid="stMetric"] {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

/* Headings */
h1 {
    color: #1b5e20 !important;
}
h2, h3 {
    color: #2e7d32 !important;
}

</style>
""", unsafe_allow_html=True)

st.title("🚀 Supply Chain Intelligence Hub")

# ---------------- BIGQUERY ----------------
client = bigquery.Client()

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

# ---------------- SIDEBAR ----------------
st.sidebar.header("🎛️ Filters")

selected_customer = st.sidebar.multiselect(
    "Select Customers",
    options=dim_customers['customer_name'].unique()
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Navigation")

page = st.sidebar.radio(
    "",
    ["📊 Dashboard", "🔍 Explore Data", "👥 People Dimension"]
)

df = fact_orders.copy()

if selected_customer:
    df = df[df['customer_name'].isin(selected_customer)]

# ---------------- DASHBOARD PAGE ----------------
if page == "📊 Dashboard":

    # ---------- PERFORMANCE OVERVIEW ----------
    st.markdown("## 📊 Performance Overview")

    total_orders = len(df)
    total_revenue = df['sales'].sum()
    avg_order_value = df['sales'].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Orders", total_orders)
    col2.metric("Total Revenue", f"${total_revenue:,.0f}")
    col3.metric("Avg Order Value", f"${avg_order_value:,.0f}")

    st.markdown("---")

    # ---------- MONTHLY SALES ----------
    st.subheader("📈 Monthly Sales Trend")

    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date'])
        monthly = (
            df.groupby(df['order_date'].dt.to_period("M"))
            .sum(numeric_only=True)
            .reset_index()
        )
        monthly['order_date'] = monthly['order_date'].dt.to_timestamp()

        fig = px.area(
            monthly,
            x='order_date',
            y='sales',
            template="simple_white",
            color_discrete_sequence=["#2e7d32"]
        )
        fig.update_traces(line=dict(width=3))
        st.plotly_chart(fig, use_container_width=True)

    # ---------- STATE ANALYSIS ----------
    if 'state' in df.columns:

        st.subheader("🗺️ State-wise Revenue Distribution")

        state_sales = df.groupby('state')['sales'].sum().reset_index()

        col1, col2 = st.columns(2)

        # ---- BAR ----
        top_states = state_sales.sort_values(
            by='sales', ascending=False
        ).head(10)

        fig_bar = px.bar(
            top_states,
            x='sales',
            y='state',
            orientation='h',
            template="simple_white",
            color='sales',
            color_continuous_scale=["#a5d6a7", "#1b5e20"]
        )
        fig_bar.update_layout(yaxis=dict(autorange="reversed"))
        col1.plotly_chart(fig_bar, use_container_width=True)

        # ---- PIE (Top 3 + Others) ----
        top3 = state_sales.sort_values(
            by='sales', ascending=False
        ).head(3)

        others = state_sales.sort_values(
            by='sales', ascending=False
        ).iloc[3:]

        if not others.empty:
            others_sum = others['sales'].sum()
            others_row = pd.DataFrame(
                [["Others", others_sum]],
                columns=['state', 'sales']
            )
            pie_data = pd.concat([top3, others_row])
        else:
            pie_data = top3

        fig_pie = px.pie(
            pie_data,
            values='sales',
            names='state',
            template="simple_white",
            hole=0.4,
            color_discrete_sequence=[
                "#1b5e20",
                "#2e7d32",
                "#43a047",
                "#81c784"
            ]
        )

        fig_pie.update_traces(
            textinfo='percent+label',
            textposition='inside'
        )

        col2.plotly_chart(fig_pie, use_container_width=True)

    # ---------- ORDER VALUE DISTRIBUTION ----------
    # --- Order Value Distribution ---
st.subheader("📦 Order Value Distribution")

if 'sales' in df.columns:

    # Clean data
    sales_data = df['sales'].dropna()

    if not sales_data.empty:

        # Remove extreme outliers for better visualization
        lower_bound = sales_data.quantile(0.01)
        upper_bound = sales_data.quantile(0.99)

        filtered_sales = sales_data[
            (sales_data >= lower_bound) &
            (sales_data <= upper_bound)
        ]

        fig = px.histogram(
            filtered_sales,
            nbins=30,
            title="Distribution of Order Values",
        )

        fig.update_layout(
            xaxis_title="Order Value ($)",
            yaxis_title="Number of Orders",
            bargap=0.1
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No sales data available for distribution view.")
# ---------------- DATA PAGE ----------------
elif page == "🔍 Explore Data":
    st.markdown("## 🔍 Data Explorer")
    st.dataframe(df)

# ---------------- PEOPLE PAGE ----------------
elif page == "👥 People Dimension":
    st.markdown("## 👥 People Dimension")
    st.dataframe(dim_people)