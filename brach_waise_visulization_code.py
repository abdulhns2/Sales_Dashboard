import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from fpdf import FPDF
import tempfile
import os
import base64
import pdfkit
from datetime import datetime
# =======================
# Database Connection
# =======================
d_db = 'Candelah_DW'
d_server = 'DESKTOP-9UQ8HVO\\CANDELASERVER'
d_driver = 'ODBC Driver 11 for SQL Server'
conn_str = f"mssql+pyodbc://@{d_server}/{d_db}?driver={d_driver}&trusted_connection=yes"
engine = create_engine(conn_str)

# =======================
# Load Data
# =======================
@st.cache_data
def load_data():
    query = """
        SELECT 
            Fact_ID, SaleLineItemID, Receipt, Shop_ID, Shop, POS, Date, Time, Day,
            [Customer Name], Product_Id, Product_code, [Product Name], Technical_details,
            [Retail Price], Quantity, Sales, [Sales Amount], Tax, [Sales + Tax], TaxCode,
            Cost, [Gross Margin (on Sales Amt)], Cash_amt, Card_amt, MOP, [Is Discounted],
            discount_name, Load_Date
        FROM Fact_Table
    """
    df = pd.read_sql(query, engine)

    df["Date"] = pd.to_datetime(df["Date"])
    df["Load_Date"] = pd.to_datetime(df["Load_Date"])
    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)
    return df

df = load_data()

# =======================
# Sidebar Filters
# =======================
st.sidebar.header("Filters")

# Radio button for shop
branch = st.sidebar.radio(
    "Select Branch",
    options=df["Shop"].unique()
)

# Month filter
month = st.sidebar.multiselect(
    "Select Month",
    options=df["YearMonth"].unique(),
    default=df["YearMonth"].unique()
)

# Apply Filters
df_filtered = df[(df["Shop"] == branch) & (df["YearMonth"].isin(month))]


# =======================
# Sidebar Filters
# =======================
# =======================
# Sidebar Filters
# =======================
# st.sidebar.header("Filters")

# # All / Custom radio button
# filter_option = st.sidebar.radio(
#     "Select View",
#     options=["All", "Custom"],
#     index=0
# )

# # Month filter (common for both All & Custom)
# month = st.sidebar.multiselect(
#     "Select Month",
#     options=df["YearMonth"].unique(),
#     default=df["YearMonth"].unique()
# )

# if filter_option == "Custom":
#     # Branch filter only for Custom
#     branch = st.sidebar.radio(
#         "Select Branch",
#         options=df["Shop"].unique()
#     )
#     df_filtered = df[(df["Shop"] == branch) & (df["YearMonth"].isin(month))]

# else:
#     # ALL = all branches but filter by month
#     df_filtered = df[df["YearMonth"].isin(month)]


# =======================
# KPIs
# =======================
st.title("📊 Sales Dashboard")

total_sales = df_filtered["Sales"].sum()
total_qty = df_filtered["Quantity"].sum()
total_tax = df_filtered["Sales + Tax"].sum()
gross_margin = df_filtered["Gross Margin (on Sales Amt)"].sum()
avg_sales = df_filtered.groupby("Receipt")["Sales"].sum().mean()



# =======================
# Custom CSS for KPI Cards
# =======================
st.markdown("""
    <style>
    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        text-align: center;
        margin: 5px;
    }
    .kpi-title {
        font-size: 16px;
        font-weight: bold;
        color: #444;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: bold;
        color: #2E86C1;
    }
    </style>
""", unsafe_allow_html=True)

# =======================
# KPI Layout
# =======================
st.markdown("## 🔑 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>💰 Total Sales</div><div class='kpi-value'>{total_sales:,.0f}</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>📦 Total Quantity</div><div class='kpi-value'>{total_qty:,}</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🧾 Sales With Tax</div><div class='kpi-value'>{total_tax:,.0f}</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>📈 Gross Margin</div><div class='kpi-value'>{gross_margin:,.0f}</div></div>", unsafe_allow_html=True)

col5, col6, col7 = st.columns(3)
with col5:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>🔹 Avg. Sales / Receipt</div><div class='kpi-value'>{avg_sales:,.0f}</div></div>", unsafe_allow_html=True)

# =======================
# Graphs
# =======================

st.subheader("📅 Month-wise Sales Trend")
sales_trend = df_filtered.groupby("YearMonth")["Sales Amount"].sum().reset_index()
fig = px.line(sales_trend, x="YearMonth", y="Sales Amount", markers=True, title="Month-wise Sales")
st.plotly_chart(fig, use_container_width=True)

st.subheader("💻 POS-wise Performance")
pos_sales = df_filtered.groupby("POS")["Sales"].sum().reset_index()
fig = px.bar(pos_sales, x="POS", y="Sales", title="Sales by POS")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📆 Day of Week Sales")
day_sales = df_filtered.groupby("Day")["Sales"].sum().reset_index()
fig = px.bar(day_sales, x="Day", y="Sales", title="Sales by Day of Week")
st.plotly_chart(fig, use_container_width=True)

st.subheader("💳 Payment Method Split")
mop_sales = df_filtered.groupby("MOP")["Sales"].sum().reset_index()
fig = px.pie(mop_sales, names="MOP", values="Sales", title="Sales by Payment Method")
st.plotly_chart(fig, use_container_width=True)

# st.subheader("🍔 Top 30 Products by Sales")
# top_products = df_filtered.groupby("Product Name")["Sales"].sum().reset_index().nlargest(30, "Sales")
# fig = px.bar(top_products, x="Sales", y="Product Name", orientation="h", title="Top 30 Products")
# st.plotly_chart(fig, use_container_width=True)

st.subheader("🍔 Top 30 Products by Sales")

# Group by product, sum sales and quantity sold
top_products = df_filtered.groupby("Product Name").agg({
    "Sales": "sum",
    "Quantity": "sum"  # make sure your dataframe has a 'Quantity' column
}).reset_index()

# Get top 30 products by sales
top_products = top_products.nlargest(30, "Sales")

# Show in a bar chart
fig = px.bar(
    top_products,
    x="Sales",
    y="Product Name",
    orientation="h",
    text="Quantity",  # display quantity sold on bars
    title="Top 30 Products"
)
fig.update_traces(texttemplate='%{text}', textposition='inside')
st.plotly_chart(fig, use_container_width=True)

# Optional: show as a table below the chart
st.dataframe(top_products)

st.subheader("🧑 Customer-wise Sales (Selected)")
selected_customers = ["Dine IN", "Takeaway", "Delivery", "Food Panda"]
customer_sales = (
    df_filtered[df_filtered["Customer Name"].isin(selected_customers)]
    .groupby("Customer Name")["Sales"]
    .sum()
    .reset_index()
)
fig = px.bar(
    customer_sales,
    x="Customer Name",
    y="Sales",
    text="Sales",
    title="Sales by Customer Type (Dine IN, Takeaway, Delivery, Food Panda)"
)
fig.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
st.plotly_chart(fig, use_container_width=True)


st.subheader("📈 Year-wise Sales")

# Ensure Date column is datetime type
df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])

# Extract year from date
df_filtered['Year'] = df_filtered['Date'].dt.year

# Group by year and sum sales
yearly_sales = df_filtered.groupby('Year')['Sales'].sum().reset_index()

# Plot a line chart
fig = px.line(
    yearly_sales,
    x='Year',
    y='Sales',
    markers=True,
    title="Year-wise Sales"
)
fig.update_layout(yaxis_title="Sales Amount", xaxis_title="Year")
st.plotly_chart(fig, use_container_width=True)

# Optional: show as table
st.dataframe(yearly_sales)



# =======================
# Generate PDF Report
# =======================

# =======================
# Aggregations for Report
# =======================
branch_sales = df_filtered.groupby("Shop")["Sales"].sum().reset_index()
# top_products_sales = df_filtered.groupby("Product Name")["Sales"].sum().reset_index().nlargest(30, "Sales")
payment_summary = df_filtered.groupby("MOP")["Sales"].sum().reset_index()

# ----------------- Generate PDF Report -----------------
def generate_report_html():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Encode logo image to base64
    logo_path = "E:\\ETL-Pipeline\\image.png"  # <- Adjust path if needed
    with open(logo_path, "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    def format_currency(value):
        return f"PKR {int(value):,}"

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                padding: 30px;
                color: #333;
                background-color: #fff;
            }}
            .header {{
                display: flex;
                align-items: center;
                gap: 20px;
                margin-bottom: 30px;
            }}
            .logo {{
                height: 80px;
                width: 80px;
                border-radius: 10px;
                object-fit: contain;
            }}
            h1 {{ color: #2E86C1; margin: 0; font-size: 28px; }}
            h2 {{ color: #117A65; border-bottom: 1px solid #ccc; padding-bottom: 5px; margin-top: 40px; }}
            .kpi {{ margin-bottom: 10px; font-size: 16px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; }}
            th {{ background-color: #f0f0f0; }}
            .footer {{ margin-top: 50px; font-size: 14px; color: #555; }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="data:image/png;base64,{logo_base64}" class="logo" />
            <div>
                <h1>Sales Report</h1>
                <p><strong>Generated:</strong> {current_time}</p>
            </div>
        </div>

        <h2>KPI Summary</h2>
        <div class="kpi"><strong>Total Sales:</strong> {format_currency(total_sales)}</div>
        <div class="kpi"><strong>Gross Margin:</strong> {gross_margin:,.0f}</div>
        <div class="kpi"><strong>Total Sales with Tax:</strong> {total_tax:,.0f}</div>
        <div class="kpi"><strong>Avg Sales/Receipt:</strong> {avg_sales:,.0f}</div>
   


        <h2>Branch Sales</h2>
        {branch_sales.to_html(index=False)}

        <h2>Top Products by Sales</h2>
        {top_products.to_html(index=False)}

        <h2>Payment Summary</h2>
        {payment_summary.to_html(index=False)}

        <h2>Customer Wise Sales</h2>
        {customer_sales.to_html(index=False)}

        <h2>Year Wise Sales</h2>
        {yearly_sales.to_html(index=False)}

        <div class="footer">
            <p>Generated by <strong>Sales Dashboard</strong> | Powered by Hot N Spicy</p>
        </div>
    </body>
    </html>
    """
    return html

# ----------------- Export Button -----------------
if st.button("📄 Generate PDF Report"):
    try:
        html = generate_report_html()
        pdf_file_path = "Sales_Report.pdf"
        path_wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"  # Update if needed
        config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

        pdfkit.from_string(html, pdf_file_path, configuration=config)

        with open(pdf_file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')

        href = f'<a href="data:application/octet-stream;base64,{base64_pdf}" download="Sales_Report.pdf">📥 Click to Download Sales Report</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("✅ PDF report generated successfully.")
    except Exception as e:
        st.error(f"❌ Failed to generate PDF: {e}")
