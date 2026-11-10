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
# 2. DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
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
            'dest_lat': [-8.3, -23.5, -20.3], 'dest_lng': [-35.5, -46.6, -40.3],
            'Carreta_Count': [1, 0, 2], 'Toco_Count': [0, 1, 0], 'VUC_Count': [0, 0, 1]
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
st.sidebar.subheader("🔍 Node Explorer")

# Create a dropdown search bar for Customer Nodes
all_customers = sorted(od_matrix['demand_node_id'].unique())
selected_customers = st.sidebar.multiselect(
    "Lookup Customer Node(s):", 
    options=all_customers,
    help="Select one or multiple nodes. Leave blank to view the entire network."
)

st.sidebar.markdown("---")
st.sidebar.info("Model Engine: PuLP (CBC Solver)\n\nClustering: DBSCAN (Eps=50km)")

# -----------------------------------------------------------------------------
# 4. EXECUTIVE KPI RIBBON
# -----------------------------------------------------------------------------
# FILTER LOGIC: If a user selects specific customers, filter the entire dataframe first
if len(selected_customers) > 0:
    od_matrix = od_matrix[od_matrix['demand_node_id'].isin(selected_customers)]

# RECALCULATION LOGIC: Multiply slider rates by truck counts and route distance
if 'Carreta_Count' in od_matrix.columns:
    od_matrix['Dyn_Cost_RS'] = (
        (od_matrix['Carreta_Count'] * carreta_rate * od_matrix['distance_km']) +
        (od_matrix['Toco_Count'] * toco_rate * od_matrix['distance_km']) +
        (od_matrix['VUC_Count'] * vuc_rate * od_matrix['distance_km'])
    )

# Calculate totals for the dashboard display based on the active filter
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
# 5. GEOSPATIAL VISUALIZATION (TABS FOR 3 MAPS)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🏭 Origin Hubs", "🎯 Demand Regions", "🕸️ Logistics Corridors"])

# MAP 1: SELLER / PLANT NODES
with tab1:
    st.subheader("Consolidated Seller Hubs (Plant Nodes)")
    brazil_map1 = folium.Map(location=[-15.7801, -47.9292], zoom_start=4) 
    
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
        folium.PolyLine(
            locations=[[row['origin_lat'], row['origin_lng']], [row['dest_lat'], row['dest_lng']]],
            weight=2, color='#0000FF', opacity=0.5,
            tooltip=(f"Route: Node {row['plant_node_id']} to {row['demand_node_id']}<br>"
                     f"Payload: {row['lane_payload_tons']:.1f} Tons")
        ).add_to(brazil_map3)
        
    st_folium(brazil_map3, width=1200, height=500, key="map3")

st.markdown("---")
# -----------------------------------------------------------------------------
# 6. TACTICAL OPERATIONS & UNIT ECONOMICS
# -----------------------------------------------------------------------------
st.subheader("Tactical Route Analysis & Unit Economics")

# Calculate Unit Economics (From your notes: Price of 1m³/1km and 1kg/1km)
# (lane_payload_tons * 1000 converts tons to kg)
od_matrix['Cost_per_m3_km (R$)'] = (od_matrix['Dyn_Cost_RS'] / (od_matrix['lane_cube_m3'] * od_matrix['distance_km'])).round(4)
od_matrix['Cost_per_kg_km (R$)'] = (od_matrix['Dyn_Cost_RS'] / ((od_matrix['lane_payload_tons'] * 1000) * od_matrix['distance_km'])).round(4)

chart_col, table_col = st.columns([1, 1])

with chart_col:
    # Highest Contributors Logic
    # If no specific customer is selected, show the most expensive demand nodes overall
    if len(selected_customers) == 0:
        top_contributors = od_matrix.groupby('demand_node_id')['Dyn_Cost_RS'].sum().reset_index()
        top_contributors = top_contributors.nlargest(10, 'Dyn_Cost_RS')
        top_contributors['Node_Label'] = "Node " + top_contributors['demand_node_id'].astype(str)
        
        fig = px.bar(
            top_contributors, 
            x='Dyn_Cost_RS', 
            y='Node_Label', 
            orientation='h',
            title="Highest Contributors: Top 10 Nodes by Freight Spend",
            color_discrete_sequence=['#FF3366']
        )
    # If customers are selected, show their heaviest routes
    else:
        top_contributors = od_matrix.nlargest(10, 'lane_payload_tons').copy()
        top_contributors['Route_Name'] = top_contributors['plant_node_id'].astype(str) + " ➡️ " + top_contributors['demand_node_id'].astype(str)
        
        fig = px.bar(
            top_contributors, 
            x='lane_payload_tons', 
            y='Route_Name', 
            orientation='h',
            title="Top Routes for Selected Node(s) by Weight (Tons)",
            color_discrete_sequence=['#00FFCC']
        )

    fig.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with table_col:
    st.markdown("**Lane Unit Economics (Sortable)**")
    display_df = od_matrix[['plant_node_id', 'demand_node_id', 'distance_km', 'Dyn_Cost_RS', 'Cost_per_m3_km (R$)', 'Cost_per_kg_km (R$)']]
    
    st.dataframe(
        display_df.sort_values('Dyn_Cost_RS', ascending=False).head(20),
        use_container_width=True,
        hide_index=True
    )


# -----------------------------------------------------------------------------
# 7. PREDICTIVE SCENARIO CALCULATOR
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🔮 Predictive Scenario Calculator")
st.markdown("Simulate the optimal fleet mix and cost for a custom shipment size.")

scen_col1, scen_col2, scen_col3 = st.columns(3)
with scen_col1:
    sim_vol = st.number_input("Shipment Volume (m³)", min_value=0.0, value=120.0, step=10.0)
with scen_col2:
    sim_weight = st.number_input("Shipment Weight (Tons)", min_value=0.0, value=30.0, step=1.0)
with scen_col3:
    sim_dist = st.number_input("Route Distance (km)", min_value=1.0, value=500.0, step=50.0)

# Lightweight heuristic optimization for the simulator
# (Assuming standard Brazilian truck capacities - adjustable if your MILP differs)
vol_rem, wt_rem = sim_vol, sim_weight
sim_carreta = sim_toco = sim_vuc = 0

# Greedy allocation prioritizing the largest truck
while vol_rem > 45 or wt_rem > 14:  # More than a Toco can handle
    sim_carreta += 1
    vol_rem = max(0, vol_rem - 95)  # Carreta capacity: 95 m3
    wt_rem = max(0, wt_rem - 25)    # Carreta capacity: 25 Tons

while vol_rem > 15 or wt_rem > 4:   # More than a VUC can handle
    sim_toco += 1
    vol_rem = max(0, vol_rem - 45)  # Toco capacity: 45 m3
    wt_rem = max(0, wt_rem - 14)    # Toco capacity: 14 Tons

if vol_rem > 0 or wt_rem > 0:
    sim_vuc += 1                    # VUC covers the remainder

# Calculate predicted cost using the live slider rates
sim_cost = (sim_carreta * carreta_rate * sim_dist) + (sim_toco * toco_rate * sim_dist) + (sim_vuc * vuc_rate * sim_dist)

# Display the prediction result
st.success(f"**Optimal Fleet Required:** {sim_carreta} Carretas, {sim_toco} Tocos, {sim_vuc} VUCs")
st.info(f"**Estimated Freight Cost:** R$ {sim_cost:,.2f}")
