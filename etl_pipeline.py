import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

st.set_page_config(page_title="📦 Interactive Retail Sales Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center; color: #4CAF50;'>📦 Online Retail Sales Dashboard (Interactive)</h1>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('output/cleaned_online_retail.csv', parse_dates=['InvoiceDate'])
    return df

df = load_data()

# Sidebar Filters
with st.sidebar:
    st.header("📂 Filters")
    min_date, max_date = df['InvoiceDate'].min(), df['InvoiceDate'].max()
    date_range = st.date_input("📅 Date Range", [min_date, max_date])

    df = df[(df['InvoiceDate'] >= pd.Timestamp(date_range[0])) & (df['InvoiceDate'] <= pd.Timestamp(date_range[1]))]

    countries = st.multiselect("🌍 Select Country", df['Country'].unique(), default=['United Kingdom'])
    df = df[df['Country'].isin(countries)]

    products = st.multiselect("📦 Select Product", df['Description'].unique())
    if products:
        df = df[df['Description'].isin(products)]

    cust_id = st.text_input("👥 CustomerID (Optional)")
    if cust_id:
        df = df[df['CustomerID'].astype(str).str.contains(cust_id)]

    quantity_min, quantity_max = st.slider("🔢 Quantity Range", int(df['Quantity'].min()), int(df['Quantity'].max()), (int(df['Quantity'].min()), int(df['Quantity'].max())))
    df = df[(df['Quantity'] >= quantity_min) & (df['Quantity'] <= quantity_max)]

# KPIs
with st.container():
    st.subheader("📊 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Sales (£)", f"{df['TotalPrice'].sum():,.2f}")
    col2.metric("🛒 Orders", df['InvoiceNo'].nunique())
    col3.metric("👥 Customers", df['CustomerID'].nunique())
    col4.metric("📦 Products", df['Description'].nunique())

# Tabs for Interactive Charts
tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Products", "📅 Sales Over Time", "🌍 Sales by Country", "🥧 Customer Distribution"])

with tab1:
    st.subheader("🏆 Top 10 Products by Sales")
    top_products = df.groupby('Description')['TotalPrice'].sum().sort_values(ascending=False).head(10).reset_index()
    fig1 = px.bar(top_products, x='TotalPrice', y='Description', orientation='h', color='TotalPrice', color_continuous_scale='viridis', title="Top 10 Products by Sales")
    fig1.update_layout(yaxis_title='Product', xaxis_title='Total Sales (£)', height=500)
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("📅 Sales Over Time")
    sales_over_time = df.groupby('InvoiceDate')['TotalPrice'].sum().reset_index()
    fig2 = px.line(sales_over_time, x='InvoiceDate', y='TotalPrice', title="Sales Trend Over Time", markers=True)
    fig2.update_layout(xaxis_title='Date', yaxis_title='Total Sales (£)', height=500)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("🌍 Sales Over Time by Country")
    fig3 = go.Figure()
    for c in df['Country'].unique():
        country_sales = df[df['Country'] == c].groupby('InvoiceDate')['TotalPrice'].sum().reset_index()
        fig3.add_trace(go.Scatter(x=country_sales['InvoiceDate'], y=country_sales['TotalPrice'], mode='lines+markers', name=c))
    fig3.update_layout(title="Sales Over Time by Country", xaxis_title='Date', yaxis_title='Total Sales (£)', height=500)
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("🥧 Customer Distribution by Country")
    customer_distribution = df.groupby('Country')['CustomerID'].nunique().sort_values(ascending=False)
    top5 = customer_distribution.head(5)
    others = customer_distribution.iloc[5:].sum()
    final_distribution = pd.concat([top5, pd.Series({'Others': others})]).reset_index()
    fig4 = px.pie(final_distribution, values=0, names='index', title="Customer Distribution by Country (Top 5 + Others)", color_discrete_sequence=px.colors.sequential.RdBu)
    fig4.update_traces(textinfo='percent+label')
    st.plotly_chart(fig4, use_container_width=True)

