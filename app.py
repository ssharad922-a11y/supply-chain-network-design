import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Supply Chain Optimization | Olist",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme metric cards
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚛 Brazil Supply Chain Network Design")
st.markdown("Mixed-Integer Linear Programming (MILP) Fleet Optimization Model")

# -----------------------------------------------------------------------------
# 2. DATA LOADING (Using the CSVs we generated)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # Replace these with your actual file names
    try:
        od_matrix = pd.read_csv('Optimized_Shipping_Lanes.csv')
        origins = pd.read_csv('Origin_Hub_Constraints.csv')
    except FileNotFoundError:
        # Failsafe mock data just in case the CSVs aren't in the folder yet
        od_matrix = pd.DataFrame({
            'plant_node_id': [0, 14, 2], 'demand_node_id': [45, 14, 11],
            'lane_payload_tons': [15.0, 8.5, 22.1], 'lane_cube_m3': [37.8, 12.1, 85.0],
            'distance_km': [2040, 45, 850], 'Dyn_Cost_RS': [1350, 450, 2100],
            'origin_lat': [-22.9, -23.5, -19.9], 'origin_lng': [-47.1, -46.6, -44.1],
            'dest_lat': [-8.3, -23.5, -20.3], 'dest_lng': [-35.5, -46.6, -40.3]
        })
    return od_matrix

od_matrix = load_data()

# -----------------------------------------------------------------------------
# 3. SIDEBAR: THE CONTROL PANEL
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Logistics Parameters")
st.sidebar.markdown("Adjust freight rates to simulate network changes.")

carreta_rate = st.sidebar.slider("Carreta Rate (R$/km)", min_value=5.0, max_value=15.0, value=8.5, step=0.5)
toco_rate = st.sidebar.slider("Toco Rate (R$/km)", min_value=3.0, max_value=10.0, value=5.5, step=0.5)
vuc_rate = st.sidebar.slider("VUC Rate (R$/km)", min_value=1.0, max_value=7.0, value=3.5, step=0.5)

st.sidebar.markdown("---")
st.sidebar.info("Model Engine: PuLP (CBC Solver)\n\nClustering: DBSCAN (Eps=50km)")

# -----------------------------------------------------------------------------
# 4. EXECUTIVE KPI RIBBON
# -----------------------------------------------------------------------------
# Calculate mock totals for the dashboard display
total_volume = od_matrix['lane_cube_m3'].sum()
total_weight = od_matrix['lane_payload_tons'].sum()
total_distance = od_matrix['distance_km'].sum()
total_cost = od_matrix['Dyn_Cost_RS'].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Volume (m³)", f"{total_volume:,.0f}")
col2.metric("Total Weight (Tons)", f"{total_weight:,.1f}")
col3.metric("Total Route Length (km)", f"{total_distance:,.0f}")
col4.metric("Total Freight Spend (R$)", f"R$ {total_cost:,.2f}")

st.markdown("---")

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# 5. GEOSPATIAL VISUALIZATION (TABS FOR 3 MAPS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🏭 Origin Hubs", "🎯 Demand Regions", "🕸️ Logistics Corridors"])

# MAP 1: SSELLERS / PLANT NODES
with tab1:
    st.subheader("Consolidated Seller Hubs (Plant Nodes)")
    brazil_map1 = folium.Map(location=[-15.7801, -47.9292], zoom_start=4) # Default OpenStreetMap
    
    # Extract unique origin locations to plot the hubs
    origins_df = od_matrix.drop_duplicates(subset=['plant_node_id'])
    
    for index, row in origins_df.iterrows():
        folium.CircleMarker(
            location=[row['origin_lat'], row['origin_lng']],
            radius=8, color='#FF3366', fill=True, fill_opacity=0.7,
            tooltip=f"Seller Hub Node: {row['plant_node_id']}"
        ).add_to(brazil_map1)
        
    st_folium(brazil_map1, width=1200, height=500, key="map1")

# MAP 2: CUSTOMERS / DEMAND NODES
with tab2:
    st.subheader("Regional Customer Centers (Demand Nodes)")
    brazil_map2 = folium.Map(location=[-15.7801, -47.9292], zoom_start=4)
    
    # Extract unique destination locations to plot the customers
    destinations_df = od_matrix.drop_duplicates(subset=['demand_node_id'])
    
    for index, row in destinations_df.iterrows():
        folium.CircleMarker(
            location=[row['dest_lat'], row['dest_lng']],
            radius=5, color='#33CCFF', fill=True, fill_opacity=0.7,
            tooltip=f"Customer Region Node: {row['demand_node_id']}"
        ).add_to(brazil_map2)
        
    st_folium(brazil_map2, width=1200, height=500, key="map2")

# MAP 3: LOGISTICS CORRIDORS
with tab3:
    st.subheader("High-Density Shipping Lanes")
    brazil_map3 = folium.Map(location=[-15.7801, -47.9292], zoom_start=4)
    
    for index, row in od_matrix.head(50).iterrows():
        # Draw the shipping lane
        folium.PolyLine(
            locations=[[row['origin_lat'], row['origin_lng']], [row['dest_lat'], row['dest_lng']]],
            weight=2, color='#0000FF', opacity=0.5,
            tooltip=(f"Route: Node {row['plant_node_id']} to {row['demand_node_id']}<br>"
                     f"Payload: {row['lane_payload_tons']:.1f} Tons")
        ).add_to(brazil_map3)
        
    st_folium(brazil_map3, width=1200, height=500, key="map3")

st.markdown("---")
# -----------------------------------------------------------------------------
# 6. TACTICAL OPERATIONS (CHARTS & TABLES)
# -----------------------------------------------------------------------------
st.subheader("Tactical Route Analysis")
chart_col, table_col = st.columns([1, 1])

with chart_col:
    # 6A. Horizontal Bar Chart (Top 10 Routes by Payload)
    top_10_chart = od_matrix.nlargest(10, 'lane_payload_tons').copy()
    top_10_chart['Route_Name'] = top_10_chart['plant_node_id'].astype(str) + " ➡️ " + top_10_chart['demand_node_id'].astype(str)
    
    fig = px.bar(
        top_10_chart, 
        x='lane_payload_tons', 
        y='Route_Name', 
        orientation='h',
        title="Top 10 Routes by Freight Weight (Tons)",
        color_discrete_sequence=['#00FFCC']
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with table_col:
    # 6B. Sortable Dataframe
    st.markdown("**Top Shipping Lanes (Sortable)**")
    display_df = od_matrix[['plant_node_id', 'demand_node_id', 'distance_km', 'lane_payload_tons', 'Dyn_Cost_RS']]
    
    # Use Streamlit's native interactive dataframe
    st.dataframe(
        display_df.sort_values('Dyn_Cost_RS', ascending=False).head(20),
        use_container_width=True,
        hide_index=True
    )