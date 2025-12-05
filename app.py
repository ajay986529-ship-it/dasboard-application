

import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np # Added numpy import

# --- Page Configuration and Amazon-like Styling ---
st.set_page_config(
    page_title="Amazon Seller Central Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Amazon Seller Central look and feel
st.markdown("""
<style>
    /* Main background */
    .stApp { 
        background-color: white;
    }
    /* Header/Top Bar (not directly controlable without custom HTML, but can style elements) */
    /* Sidebar */
    .stSidebar > div:first-child {
        background-color: #131A22; /* Navy */
        color: white;
    }
    .stSidebar .stRadio div[role="radiogroup"] label {
        color: white; /* Sidebar navigation text */
    }
    .stSidebar .stRadio div[role="radiogroup"] label:hover {
        background-color: #FF9900; /* Orange on hover */
        color: white;
    }
    .stSidebar .stRadio div[role="radiogroup"] label.st-dg {
        background-color: #FF9900; /* Selected item orange */
        color: white;
        border-radius: 5px;
    }
    /* Streamlit components styling */
    .stButton>button {
        background-color: #FF9900; /* Orange buttons */
        color: white;
        border-radius: 5px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #e68a00; /* Darker orange on hover */
    }
    .css-1d391kg.e16zqm1j1 {
        background-color: #f0f2f6; /* Light grey for widgets background */
        padding: 1rem;
        border-radius: 10px;
    }
    /* KPI Cards Styling */
    .kpi-card {
        background-color: #f8f8f8;
        border-left: 5px solid #FF9900; /* Orange accent */
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .kpi-title {
        font-size: 1.1em;
        color: #555;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 2em;
        font_weight: bold;
        color: #131A22; /* Navy */
    }
    /* General spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    /* Adjust main content padding for a cleaner look */
    .css-1lcbmhc, .css-z5fcl4 {
        padding-left: 1rem; /* Reduce left/right padding */
        padding-right: 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #131A22;
    }
    .reportview-container .main .block-container{
        padding-top: 1rem; /* Adjust padding for content at top */
    }
</style>""", unsafe_allow_html=True)

# --- Data Loading and Preprocessing ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('/content/amazon.csv')
        
        # Convert 'Date' column to datetime objects
        if 'Date' in df.columns:
            # Add errors='coerce' to turn unparseable dates into NaT
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            # Fill NaT values with a default date to avoid NaNs in dt.month
            if df['Date'].isnull().any():
                st.warning("Some dates in 'Date' column were unparseable and converted to NaT. Filling with '2022-01-01' for calculations.")
                df['Date'] = df['Date'].fillna(pd.to_datetime('2022-01-01'))
        else:
            # Generate dummy dates if 'Date' is missing
            st.warning(" 'Date' column not found, generating dummy dates.")
            df['Date'] = pd.date_range(start='2022-01-01', periods=len(df), freq='D')
            
        # Ensure necessary columns exist for the dashboard
        required_cols = [
            'Date', 'Marketplace', 'Category', 'ASIN', 'Title',
            'Sessions', 'Units Sold', 'Revenue'
        ]
        for col in required_cols:
            if col not in df.columns:
                st.warning(f"'{col}' column not found. Generating dummy data for it.")
                if col == 'Marketplace':
                    df[col] = pd.Series(["US", "UK", "DE"]).sample(n=len(df), replace=True).values
                elif col == 'Category':
                    df[col] = pd.Series(["Electronics", "Books", "Home & Kitchen", "Apparel"]).sample(n=len(df), replace=True).values
                elif col == 'ASIN':
                    df[col] = [f'B0{i:08d}' for i in range(len(df))]
                elif col == 'Title':
                    df[col] = [f'Product Title {i}' for i in range(len(df))]
                elif col == 'Sessions':
                    # Ensure the result is numeric before casting to int and handle index alignment
                    sampled_sessions = pd.Series(range(100, 10000)).sample(n=len(df), replace=True).values
                    df[col] = (sampled_sessions * (1 + df['Date'].dt.month / 12)).fillna(0).astype(int)
                elif col == 'Units Sold':
                    # Ensure the result is numeric before casting to int and handle index alignment
                    sampled_units_sold = pd.Series(range(10, 500)).sample(n=len(df), replace=True).values
                    df[col] = (sampled_units_sold * (1 + df['Date'].dt.month / 12)).fillna(0).astype(int)
                elif col == 'Revenue':
                    # Ensure index alignment for sampled prices
                    sampled_prices = pd.Series(range(10, 200)).sample(n=len(df), replace=True).values
                    df[col] = df['Units Sold'] * sampled_prices

        # Generate additional columns if not present
        if 'Orders' not in df.columns:
            # Ensure the result is numeric before casting to int
            df['Orders'] = (df['Units Sold'] * 0.7).fillna(0).astype(int) # Dummy Orders
        if 'Buy Box %' not in df.columns:
            # Ensure index alignment for sampled Buy Box %
            df['Buy Box %'] = pd.Series([0.6, 0.7, 0.8, 0.9]).sample(n=len(df), replace=True, weights=[0.1, 0.2, 0.3, 0.4]).values # Dummy Buy Box %
        if 'Profit' not in df.columns:
            df['Profit'] = df['Revenue'] * 0.25 # Dummy Profit Margin
        if 'Traffic Source' not in df.columns:
            # Ensure index alignment for sampled Traffic Source
            df['Traffic Source'] = pd.Series(["Organic", "Paid Search", "Social Media", "Direct"]).sample(n=len(df), replace=True).values
            
        # Calculate Conversion Rate
        df['Conversion Rate'] = (df['Units Sold'] / df['Sessions']).fillna(0) * 100
        
        return df
    except FileNotFoundError:
        st.error("amazon.csv not found. Please upload the file or ensure it's in the correct path.")
        return pd.DataFrame() # Return empty DataFrame on error

df = load_data()

if df.empty:
    st.stop() # Stop if data loading failed

# --- Sidebar Navigation and Filters ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", width=100) # Placeholder Amazon logo
    st.title("Seller Central")

    st.header("Navigation")
    selected_page = st.radio(
        "",
        ("Overview", "Sales", "Products", "Traffic", "Finance")
    )

    st.header("Filters")
    
    # Date Range Picker
    min_date = df['Date'].min().to_pydatetime() if not df.empty else datetime.date.today() - datetime.timedelta(days=365)
    max_date = df['Date'].max().to_pydatetime() if not df.empty else datetime.date.today()

    start_date, end_date = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Convert selected dates to datetime objects for filtering
    start_date = datetime.datetime.combine(start_date, datetime.time.min)
    end_date = datetime.datetime.combine(end_date, datetime.time.max)

    # Marketplace Selector
    all_marketplaces = ['All'] + list(df['Marketplace'].unique())
    selected_marketplace = st.selectbox("Marketplace", all_marketplaces)

    # Category Dropdown
    all_categories = ['All'] + list(df['Category'].unique())
    selected_categories = st.multiselect("Category", all_categories, default=all_categories[1:] if len(all_categories) > 1 else [])

# Filter data based on selections
filtered_df = df[
    (df['Date'] >= start_date) &
    (df['Date'] <= end_date)
]

if selected_marketplace != 'All':
    filtered_df = filtered_df[filtered_df['Marketplace'] == selected_marketplace]

if 'All' not in selected_categories and selected_categories:
    filtered_df = filtered_df[filtered_df['Category'].isin(selected_categories)]

# --- Main Content Area ---
st.title(f"{selected_page}")

if selected_page == "Overview":
    st.subheader("Key Performance Indicators")

    if not filtered_df.empty:
        total_revenue = filtered_df['Revenue'].sum()
        total_orders = filtered_df['Orders'].sum()
        total_units_sold = filtered_df['Units Sold'].sum()
        total_sessions = filtered_df['Sessions'].sum()
        avg_conversion_rate = filtered_df['Conversion Rate'].mean()

        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Revenue</div>
                <div class="kpi-value">${total_revenue:,.2f}</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Orders</div>
                <div class="kpi-value">{total_orders:,}</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Units Sold</div>
                <div class="kpi-value">{total_units_sold:,}</div>
            </div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Sessions</div>
                <div class="kpi-value">{total_sessions:,}</div>
            </div>""", unsafe_allow_html=True)
        with col5:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Conversion Rate</div>
                <div class="kpi-value">{avg_conversion_rate:.2f}%</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No data available for the selected filters.")

elif selected_page == "Sales":
    st.subheader("Sales Performance")

    if not filtered_df.empty:
        # Daily Sales Line Chart
        daily_sales = filtered_df.groupby(filtered_df['Date'].dt.date)['Revenue'].sum().reset_index()
        daily_sales['Date'] = pd.to_datetime(daily_sales['Date'])
        fig_daily_sales = px.line(
            daily_sales,
            x='Date',
            y='Revenue',
            title='Daily Sales Trend',
            color_discrete_sequence=['#FF9900'] # Amazon orange
        )
        fig_daily_sales.update_layout(hovermode="x unified", title_x=0.5, xaxis_title="", yaxis_title="Revenue")
        st.plotly_chart(fig_daily_sales, use_container_width=True)

        # Category Performance Bar Chart
        category_performance = filtered_df.groupby('Category')['Revenue'].sum().reset_index().sort_values(by='Revenue', ascending=False)
        fig_category = px.bar(
            category_performance,
            x='Category',
            y='Revenue',
            title='Revenue by Category',
            color='Category',
            color_discrete_sequence=px.colors.sequential.YlOrBr # Orange-ish palette
        )
        fig_category.update_layout(title_x=0.5, xaxis_title="", yaxis_title="Revenue")
        st.plotly_chart(fig_category, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

elif selected_page == "Products":
    st.subheader("Product Performance")

    if not filtered_df.empty:
        # Aggregate product data for the table
        product_table_df = filtered_df.groupby(['ASIN', 'Title']).agg(
            Sessions=('Sessions', 'sum'),
            Buy_Box_Win_Rate=('Buy Box %', 'mean'), # Assuming Buy Box % is per entry, average it
            Units_Sold=('Units Sold', 'sum'),
            Revenue=('Revenue', 'sum'),
            Profit=('Profit', 'sum')
        ).reset_index()
        
        # Format Buy_Box_Win_Rate as percentage
        product_table_df['Buy_Box_Win_Rate'] = product_table_df['Buy_Box_Win_Rate'].apply(lambda x: f"{x:.2%}")

        # Rename columns for display
        product_table_df.rename(columns={
            'Buy_Box_Win_Rate': 'Buy Box %'
        }, inplace=True)
        
        st.dataframe(product_table_df.sort_values(by='Revenue', ascending=False), use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

elif selected_page == "Traffic":
    st.subheader("Traffic Source Analysis")

    if not filtered_df.empty:
        # Traffic Sources Pie Chart
        traffic_sources = filtered_df.groupby('Traffic Source')['Sessions'].sum().reset_index()
        fig_traffic = px.pie(
            traffic_sources,
            values='Sessions',
            names='Traffic Source',
            title='Sessions by Traffic Source',
            color_discrete_sequence=px.colors.sequential.Oranges # Orange shades
        )
        fig_traffic.update_layout(title_x=0.5)
        st.plotly_chart(fig_traffic, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

elif selected_page == "Finance":
    st.subheader("Financial Overview")

    if not filtered_df.empty:
        total_profit = filtered_df['Profit'].sum()
        total_revenue = filtered_df['Revenue'].sum()

        st.metric(label="Total Profit", value=f"${total_profit:,.2f}")
        st.metric(label="Total Revenue", value=f"${total_revenue:,.2f}")

        # Simple line chart for profit over time
        daily_profit = filtered_df.groupby(filtered_df['Date'].dt.date)['Profit'].sum().reset_index()
        daily_profit['Date'] = pd.to_datetime(daily_profit['Date'])
        fig_profit_trend = px.line(
            daily_profit,
            x='Date',
            y='Profit',
            title='Daily Profit Trend',
            color_discrete_sequence=['#28A745'] # Green for profit
        )
        fig_profit_trend.update_layout(hovermode="x unified", title_x=0.5, xaxis_title="", yaxis_title="Profit")
        st.plotly_chart(fig_profit_trend, use_container_width=True)

    else:
        st.info("No data available for the selected filters.")
