import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO

# Set page config
st.set_page_config(
    page_title="📊 Retail Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .metric-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metric-title {
            color: #6c757d;
            font-size: 14px;
            font-weight: 600;
        }
        .metric-value {
            color: #212529;
            font-size: 24px;
            font-weight: 700;
        }
        .stSelectbox, .stMultiselect, .stSlider, .stDateInput {
            border-radius: 8px !important;
        }
        .stDataFrame {
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Load data with caching
@st.cache_data
def load_data():
    df = pd.read_csv('output/cleaned_online_retail.csv', parse_dates=['InvoiceDate'])
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
    df['Year'] = df['InvoiceDate'].dt.year
    df['Month'] = df['InvoiceDate'].dt.month_name()
    df['Day'] = df['InvoiceDate'].dt.day_name()
    df['Hour'] = df['InvoiceDate'].dt.hour
    df['TotalPrice'] = df['UnitPrice'] * df['Quantity']
    return df

df = load_data()

# Sidebar with filters
with st.sidebar:
    st.header("🔍 Filters")
    
    # Date range with quick select options
    min_date, max_date = df['InvoiceDate'].min(), df['InvoiceDate'].max()
    date_range = st.date_input(
        "📅 Date Range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Country selection
    all_countries = df['Country'].unique()
    selected_countries = st.multiselect(
        "🌍 Countries", 
        options=all_countries,
        default=['United Kingdom']
    )
    
    # Product selection
    if selected_countries:
        available_products = df[df['Country'].isin(selected_countries)]['Description'].unique()
    else:
        available_products = df['Description'].unique()
        
    selected_products = st.multiselect(
        "📦 Products (Optional)", 
        options=available_products
    )
    
    # Customer segment
    cust_segment = st.selectbox(
        "👥 Customer Segment",
        ['All', 'New', 'Repeat', 'High Value'],
        index=0
    )
    
    # Quantity filter
    min_qty, max_qty = int(df['Quantity'].min()), int(df['Quantity'].max())
    qty_range = st.slider(
        "🔢 Quantity Range", 
        min_qty, max_qty, 
        (min_qty, max_qty)
    )
    
    # Price filter
    min_price, max_price = float(df['UnitPrice'].min()), float(df['UnitPrice'].max())
    price_range = st.slider(
        "💰 Unit Price Range (£)", 
        min_price, max_price, 
        (min_price, max_price),
        step=0.1
    )
    
    # Data download
    st.markdown("---")
    if st.button("💾 Export Data"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name='retail_data.csv',
            mime='text/csv'
        )

# Apply filters
filtered_df = df[
    (df['InvoiceDate'] >= pd.Timestamp(date_range[0])) & 
    (df['InvoiceDate'] <= pd.Timestamp(date_range[1])) &
    (df['Quantity'] >= qty_range[0]) & 
    (df['Quantity'] <= qty_range[1]) &
    (df['UnitPrice'] >= price_range[0]) & 
    (df['UnitPrice'] <= price_range[1])
]

if selected_countries:
    filtered_df = filtered_df[filtered_df['Country'].isin(selected_countries)]
    
if selected_products:
    filtered_df = filtered_df[filtered_df['Description'].isin(selected_products)]
    
if cust_segment == 'New':
    first_purchases = df.groupby('CustomerID')['InvoiceDate'].min().reset_index()
    filtered_df = filtered_df.merge(first_purchases, on=['CustomerID', 'InvoiceDate'])
elif cust_segment == 'Repeat':
    repeat_customers = df.groupby('CustomerID')['InvoiceNo'].nunique()
    repeat_customers = repeat_customers[repeat_customers > 1].index
    filtered_df = filtered_df[filtered_df['CustomerID'].isin(repeat_customers)]
elif cust_segment == 'High Value':
    high_value = df.groupby('CustomerID')['TotalPrice'].sum().nlargest(100).index
    filtered_df = filtered_df[filtered_df['CustomerID'].isin(high_value)]

# KPI Cards
with st.container():
    st.subheader("📊 Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card"><div class="metric-title">Total Sales</div><div class="metric-value">£{:,.2f}</div></div>'.format(
            filtered_df['TotalPrice'].sum()), unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card"><div class="metric-title">Total Orders</div><div class="metric-value">{:,}</div></div>'.format(
            filtered_df['InvoiceNo'].nunique()), unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card"><div class="metric-title">Active Customers</div><div class="metric-value">{:,}</div></div>'.format(
            filtered_df['CustomerID'].nunique()), unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card"><div class="metric-title">Unique Products</div><div class="metric-value">{:,}</div></div>'.format(
            filtered_df['Description'].nunique()), unsafe_allow_html=True)

# Main Dashboard Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "📦 Products", "🌍 Geography", "👥 Customers"])

with tab1:
    st.subheader("Sales Trends Over Time")
    
    # Date aggregation
    date_agg = st.radio(
        "Time Period:",
        ["Daily", "Monthly", "Yearly"],
        horizontal=True
    )
    
    if date_agg == "Daily":
        date_col = 'InvoiceDate'
        group_format = '%Y-%m-%d'
    elif date_agg == "Monthly":
        date_col = 'YearMonth'
        group_format = '%Y-%m'
    else:
        date_col = 'Year'
        group_format = '%Y'
    
    # Sales trend data
    sales_trend = filtered_df.groupby(date_col)['TotalPrice'].sum().reset_index()
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(sales_trend[date_col], sales_trend['TotalPrice'], color='#4CAF50', linewidth=2)
    ax.set_title(f"Sales Trend ({date_agg} View)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Sales (£)")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    # Additional trend views
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("By Day of Week")
        dow_sales = filtered_df.groupby('Day')['TotalPrice'].sum().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        dow_sales.plot(kind='bar', color='#4CAF50', ax=ax2)
        ax2.set_title("Sales by Day of Week")
        ax2.set_ylabel("Sales (£)")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
    
    with col2:
        st.subheader("By Hour of Day")
        hour_sales = filtered_df.groupby('Hour')['TotalPrice'].sum()
        
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        hour_sales.plot(kind='line', color='#4CAF50', marker='o', ax=ax3)
        ax3.set_title("Sales by Hour of Day")
        ax3.set_ylabel("Sales (£)")
        ax3.set_xlabel("Hour")
        st.pyplot(fig3)

with tab2:
    st.subheader("Product Performance")
    
    # Product ranking options
    metric = st.radio(
        "Rank By:",
        ["Revenue", "Quantity", "Popularity"],
        horizontal=True
    )
    
    if metric == "Revenue":
        top_products = filtered_df.groupby('Description')['TotalPrice'].sum().nlargest(10)
        y_label = "Revenue (£)"
    elif metric == "Quantity":
        top_products = filtered_df.groupby('Description')['Quantity'].sum().nlargest(10)
        y_label = "Quantity Sold"
    else:
        top_products = filtered_df.groupby('Description')['InvoiceNo'].nunique().nlargest(10)
        y_label = "Number of Orders"
    
    # Plot top products
    fig, ax = plt.subplots(figsize=(12, 6))
    top_products.sort_values().plot(kind='barh', color='#4CAF50', ax=ax)
    ax.set_title(f"Top 10 Products by {metric}")
    ax.set_xlabel(y_label)
    st.pyplot(fig)
    
    # Price distribution
    st.subheader("Price Distribution")
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    filtered_df['UnitPrice'].plot(kind='box', ax=ax2, vert=False)
    ax2.set_title("Product Price Distribution")
    ax2.set_xlabel("Unit Price (£)")
    st.pyplot(fig2)

with tab3:
    st.subheader("Geographic Analysis")
    
    if len(selected_countries) > 1 or not selected_countries:
        # Country sales
        country_sales = filtered_df.groupby('Country')['TotalPrice'].sum().nlargest(20)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        country_sales.plot(kind='bar', color='#4CAF50', ax=ax)
        ax.set_title("Sales by Country")
        ax.set_ylabel("Sales (£)")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info("Select multiple countries to compare")

with tab4:
    st.subheader("Customer Insights")
    
    # Customer distribution by country
    cust_country = filtered_df.groupby('Country')['CustomerID'].nunique().nlargest(10)
    
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.pie(
        cust_country,
        labels=cust_country.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=plt.cm.Paired.colors
    )
    ax.set_title("Customer Distribution by Country (Top 10)")
    st.pyplot(fig)
    
    # Customer RFM analysis (if not filtered to new customers)
    if cust_segment != 'New':
        st.subheader("Customer RFM Analysis")
        
        last_date = filtered_df['InvoiceDate'].max() + pd.Timedelta(days=1)
        rfm = filtered_df.groupby('CustomerID').agg({
            'InvoiceDate': lambda x: (last_date - x.max()).days,
            'InvoiceNo': 'nunique',
            'TotalPrice': 'sum'
        }).rename(columns={
            'InvoiceDate': 'Recency',
            'InvoiceNo': 'Frequency',
            'TotalPrice': 'Monetary'
        })
        
        # Display RFM table
        st.dataframe(
            rfm.describe().style.format({
                'Recency': '{:.1f}',
                'Frequency': '{:.1f}',
                'Monetary': '£{:.2f}'
            }),
            use_container_width=True
        )
        
        # RFM scatter plot
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        scatter = ax2.scatter(
            rfm['Recency'],
            rfm['Frequency'],
            s=rfm['Monetary']/50,
            c=rfm['Monetary'],
            cmap='viridis',
            alpha=0.6
        )
        ax2.set_title("Customer RFM Analysis")
        ax2.set_xlabel("Recency (Days since last purchase)")
        ax2.set_ylabel("Frequency (Number of purchases)")
        plt.colorbar(scatter, label='Monetary Value (£)')
        st.pyplot(fig2)
    else:
        st.info("RFM analysis not available for new customers only")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #777; font-size: 0.9em;'>
        <p>📊 Retail Analytics Dashboard | Powered by Streamlit | Updated: {}</p>
    </div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)