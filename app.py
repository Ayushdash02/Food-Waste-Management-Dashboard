import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import mysql.connector

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="Food Waste Dashboard",
    page_icon="🍽️",
    layout="wide"
)

# ===============================
# MYSQL CONNECTION
# ===============================
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="@ADynsx62md6r",
    database="food_waste_db"
)

def run_query(query):
    return pd.read_sql(query, conn)

# ===============================
# CUSTOM CSS (🔥 PROFESSIONAL LOOK)
# ===============================
st.markdown("""
<style>
.metric-box {
    background: linear-gradient(135deg, #1f77b4, #111);
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# HEADER
# ===============================
st.markdown("""
<h1 style='text-align:center;'>🍽️ Food Waste Management Dashboard</h1>
<p style='text-align:center;color:gray;'>Smart Food Distribution & Waste Reduction</p>
""", unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center;'>🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>", unsafe_allow_html=True)

st.markdown("---")

# ===============================
# SIDEBAR FILTERS
# ===============================
st.sidebar.header("🔍 Filters")

cities = run_query("SELECT DISTINCT Location FROM food_listings_data")["Location"]
foods = run_query("SELECT DISTINCT Food_Type FROM food_listings_data")["Food_Type"]

city_filter = st.sidebar.multiselect("City", cities)
food_filter = st.sidebar.multiselect("Food Type", foods)

# date_range = st.sidebar.date_input(
#     "Select Date Range",
#     []
# )

# ===============================
# FILTER QUERY BUILDER
# ===============================
filter_query = "WHERE 1=1"

if city_filter:
    filter_query += f" AND Location IN ({','.join([f"'{c}'" for c in city_filter])})"

if food_filter:
    filter_query += f" AND Food_Type IN ({','.join([f"'{f}'" for f in food_filter])})"

# if len(date_range) == 2:
#     start, end = date_range
#     filter_query += f" AND Expiry_Date BETWEEN '{start}' AND '{end}'"

# ===============================
# NAVIGATION (🔥 TABS INSTEAD OF RADIO)
# ===============================
tab1, tab2, tab3 = st.tabs([
    "📊 Overview",
    "🌍 Geographic",
    "📊 SQL Insights"
])

# ===============================
# TAB 1: OVERVIEW
# ===============================
with tab1:

    st.subheader("📊 Key Metrics Overview")

    k1, k2, k3, k4 = st.columns(4)

    total_records = run_query(f"SELECT COUNT(*) total FROM food_listings_data {filter_query}")['total'][0]
    total_qty = run_query(f"SELECT SUM(Quantity) qty FROM food_listings_data {filter_query}")['qty'][0]
    providers = run_query("SELECT COUNT(*) p FROM providers_data")['p'][0]
    claims = run_query("SELECT COUNT(*) c FROM claims_data")['c'][0]

    def kpi_card(title, value, color):
        return f"""
        <div style="
            background: linear-gradient(135deg, {color}, #111);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            color: white;
            box-shadow: 0px 6px 20px rgba(0,0,0,0.3);
        ">
            <div style="font-size:14px;">{title}</div>
            <div style="font-size:32px; font-weight:bold;">{value}</div>
        </div>
        """

    k1.markdown(kpi_card("📦 Total Listings", total_records, "#1f77b4"), unsafe_allow_html=True)
    k2.markdown(kpi_card("🍱 Total Quantity", int(total_qty) if total_qty else 0, "#2ca02c"), unsafe_allow_html=True)
    k3.markdown(kpi_card("🏪 Providers", providers, "#ff7f0e"), unsafe_allow_html=True)
    k4.markdown(kpi_card("📊 Claims", claims, "#d62728"), unsafe_allow_html=True)

    st.markdown("---")

    # ===============================
    # TREND ANALYSIS (INSIDE TAB1 ✅)
    # ===============================
    st.subheader("📈 Trend Analysis")

    trend = run_query(f"""
    SELECT Expiry_Date, SUM(Quantity) Quantity
    FROM food_listings_data
    {filter_query}
    GROUP BY Expiry_Date
    ORDER BY Expiry_Date
    """)

    if not trend.empty:
        trend["Expiry_Date"] = pd.to_datetime(trend["Expiry_Date"], errors="coerce")
        trend["Quantity"] = pd.to_numeric(trend["Quantity"], errors="coerce")
        trend = trend.dropna()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📊 Food Quantity Over Time")
            fig_line = px.line(trend, x="Expiry_Date", y="Quantity", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

        with col2:
            st.markdown("#### 📈 Growth Pattern")
            fig_area = px.area(trend, x="Expiry_Date", y="Quantity")
            st.plotly_chart(fig_area, use_container_width=True)

    else:
        st.warning("No trend data available")

    st.markdown("---")

    # ===============================
    # FOOD DISTRIBUTION (INSIDE TAB1 ✅)
    # ===============================
    st.subheader("🥗 Food Distribution Insights")

    col1, col2 = st.columns(2)

    food_type = run_query(f"""
    SELECT Food_Type, COUNT(*) Count
    FROM food_listings_data
    {filter_query}
    GROUP BY Food_Type
    """)

    city_data = run_query(f"""
    SELECT Location, SUM(Quantity) Quantity
    FROM food_listings_data
    {filter_query}
    GROUP BY Location
    """)

    with col1:
        if not food_type.empty:
            st.markdown("#### 🥗 Food Type Distribution")
            fig_pie = px.pie(food_type, names="Food_Type", values="Count")
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        if not city_data.empty:
            st.markdown("#### 📍 City-wise Food Availability")
            fig_bar = px.bar(city_data, x="Location", y="Quantity")
            st.plotly_chart(fig_bar, use_container_width=True)

    # ===============================
    # CLAIM STATUS (NEW)
    # ===============================
    st.subheader("📊 Claims Status Overview")

    status = run_query("""
    SELECT Status, COUNT(*) Count
    FROM claims_data
    GROUP BY Status
    """)

    if not status.empty:
        fig = px.pie(
            status,
            names="Status",
            values="Count",
            hole=0.5,
            template="plotly_white"
        )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


    # ===============================
    # MEAL TYPE ANALYSIS (NEW)
    # ===============================
    st.subheader("🍽️ Meal Type Analysis")

    meal = run_query(f"""
    SELECT Meal_Type, SUM(Quantity) Quantity
    FROM food_listings_data
    {filter_query}
    GROUP BY Meal_Type
    ORDER BY Quantity DESC
    """)

    if not meal.empty:
        fig = px.bar(
            meal,
            x="Meal_Type",
            y="Quantity",
            text="Quantity",
            template="plotly_white"
        )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")


    # ===============================
    # TOP PROVIDERS (NEW)
    # ===============================
    st.subheader("🏪 Top Food Providers")

    top_providers = run_query(f"""
    SELECT Provider_ID, SUM(Quantity) Quantity
    FROM food_listings_data
    {filter_query}
    GROUP BY Provider_ID
    ORDER BY Quantity DESC
    LIMIT 5
    """)

    if not top_providers.empty:
        fig = px.bar(
            top_providers,
            x="Quantity",
            y="Provider_ID",
            orientation="h",
            text="Quantity",
            template="plotly_white"
        )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    # 🔥 Insight
    st.info(f"Top provider: {top_providers.iloc[0]['Provider_ID']}")

# ===============================
# TAB 2: MAP
# ===============================
with tab2:

    st.subheader("🌍 Geographic Insights")

    city_data = run_query(f"""
    SELECT Location, SUM(Quantity) Quantity
    FROM food_listings_data
    {filter_query}
    GROUP BY Location
    """)

    if not city_data.empty:
        city_data["Quantity"] = pd.to_numeric(city_data["Quantity"], errors="coerce")

        city_coords = {
            "Mumbai": [19.07, 72.87],
            "Delhi": [28.70, 77.10],
            "Bangalore": [12.97, 77.59],
            "Chennai": [13.08, 80.27],
            "Kolkata": [22.57, 88.36]
        }

        city_data["lat"] = city_data["Location"].map(lambda x: city_coords.get(x, [20.5, 78.9])[0])
        city_data["lon"] = city_data["Location"].map(lambda x: city_coords.get(x, [20.5, 78.9])[1])

        fig = px.scatter_map(
            city_data,
            lat="lat",
            lon="lon",
            size="Quantity",
            color="Quantity",
            hover_name="Location",
            zoom=3
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No map data available")


# ===============================
# TAB 3: SQL ANALYSIS (FIXED)
# ===============================
with tab3:

    st.subheader("📊 Advanced SQL Insights")

    questions = {
        "1. Providers & Receivers per City": """ SELECT p.City,
            COUNT(DISTINCT p.Provider_ID) AS Providers,
            COUNT(DISTINCT r.Receiver_ID) AS Receivers
            FROM providers_data p
            JOIN receivers_data r ON p.City = r.City
            GROUP BY p.City;""",

        "2. Top Provider Type": """
        SELECT provider_type, SUM(quantity) AS total_food
        FROM food_listings_data
        GROUP BY provider_type
        ORDER BY total_food DESC;
    """,
    "3. Providers Contact Info": """
        SELECT Name, Contact, City FROM providers_data;
    """,
    "4. Top Receivers": """
        SELECT Receiver_ID, COUNT(*) AS Claims
        FROM claims_data
        GROUP BY Receiver_ID
        ORDER BY Claims DESC;
    """,
    "5. Total Food Quantity": """
        SELECT SUM(Quantity) AS Total FROM food_listings_data;
    """,
    "6. City with Highest Listings": """
        SELECT Location, COUNT(*) AS Listings
        FROM food_listings_data
        GROUP BY Location
        ORDER BY Listings DESC;
    """,
    "7. Most Common Food Types": """
        SELECT Food_Type, COUNT(*) AS Count
        FROM food_listings_data
        GROUP BY Food_Type
        ORDER BY Count DESC;
    """,
    "8. Claims per Food Item": """
        SELECT Food_ID, COUNT(*) AS Claims
        FROM claims_data
        GROUP BY Food_ID;
    """,
    "9. Top Provider by Claims": """
        SELECT f.Provider_ID, COUNT(*) AS Claims
        FROM claims_data c
        JOIN food_listings_data f ON c.Food_ID = f.Food_ID
        GROUP BY f.Provider_ID
        ORDER BY Claims DESC;
    """,
    "10. Claim Status %": """
        SELECT Status, COUNT(*) AS Count
        FROM claims_data
        GROUP BY Status;
    """,
    "11. Avg Quantity per Receiver": """
        SELECT r.Name, AVG(f.Quantity) AS Avg_Quantity
        FROM claims_data c
        JOIN food_listings_data f ON c.Food_ID = f.Food_ID
        JOIN receivers_data r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name;
    """,
    "12. Most Claimed Meal Type": """
        SELECT Meal_Type, COUNT(*) AS Count
        FROM food_listings_data
        GROUP BY Meal_Type
        ORDER BY Count DESC;
    """,
    "13. Total Food by Provider": """
        SELECT Provider_ID, SUM(Quantity) AS Total
        FROM food_listings_data
        GROUP BY Provider_ID;
    """,
    "14. City with Highest Food Waste": """
        SELECT Location, SUM(Quantity) AS Total_Waste
        FROM food_listings_data
        WHERE Food_ID NOT IN (
            SELECT Food_ID FROM claims_data WHERE Status='Completed'
        )
        GROUP BY Location
        ORDER BY Total_Waste DESC;
    """,
    "15. Providers with Most Unclaimed Food": """
        SELECT Provider_ID, SUM(Quantity) AS Unclaimed_Food
        FROM food_listings_data
        WHERE Food_ID NOT IN (
            SELECT Food_ID FROM claims_data WHERE Status='Completed'
        )
        GROUP BY Provider_ID
        ORDER BY Unclaimed_Food DESC;
    """,
    "16. Top 5 Active Receivers": """
        SELECT Receiver_ID, COUNT(*) AS Claims
        FROM claims_data
        GROUP BY Receiver_ID
        ORDER BY Claims DESC
        LIMIT 5;
    """,
    "17. Food Availability by Meal Type": """
        SELECT Meal_Type, SUM(Quantity) AS Total
        FROM food_listings_data
        GROUP BY Meal_Type;
    """,
    "18. Expired vs Total Food": """
        SELECT 
        COUNT(*) AS Total,
        SUM(CASE WHEN Expiry_Date < CURDATE() THEN 1 ELSE 0 END) AS Expired
        FROM food_listings_data;
    """
    }

    selected_q = st.selectbox("Select Analysis", list(questions.keys()))
    df_q = run_query(questions[selected_q])

    st.dataframe(df_q, use_container_width=True)

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown("<center>🚀 Developed by Ayush Dash | Streamlit Dashboard</center>", unsafe_allow_html=True)