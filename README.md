# 🚛 Supply Chain Network Design & Fleet Optimization

An end-to-end supply chain network optimization model built to minimize logistics freight spend across Brazil using Mixed-Integer Linear Programming (MILP).

## 📊 The Business Problem
A static, flat-rate logistics pricing model was resulting in highly inefficient truck utilization. The baseline routing engine favored dispatching hundreds of small vans (VUCs) on long-haul routes rather than consolidating freight into heavy trucks, resulting in inflated network costs.

## 🛠️ Methodology & Architecture
1. **Network Topology (DBSCAN):** Processed the Olist e-commerce dataset to cluster thousands of individual delivery coordinates into **22 Origin Hubs (Plant Nodes)** and **46 Regional Demand Centers**, creating a highly tractable Origin-Destination matrix.
2. **Dynamic Freight Pricing:** Engineered a distance-based cost function (Haversine formula + Base Cost) to reflect true logistics economics. 
3. **Capacity-Constrained MILP (PuLP CBC Solver):** Built an optimization engine to assign the exact optimal fleet mix (Carretas, Tocos, and VUCs) across 1,012 potential shipping lanes.

## 🚀 Key Results
By injecting distance-based economics into the solver, the model successfully pivoted the network strategy. It consolidated long-haul highway routes into heavy 95m³ "Carreta" trucks, establishing an optimized baseline freight spend of **R$ 2.67M**.

## 🖥️ Interactive Dashboard
The final model is wrapped in a Streamlit application featuring:
* **Tactical Control Panel:** Adjust carrier rates (R$/km) to simulate fleet mix changes in real-time.
* **Executive KPIs:** Track total freight spend, route length, and payload metrics.
* **Geospatial Visualization:** Interactive Folium maps rendering origin hubs, demand nodes, and high-density logistics corridors.



##Link for dashboard
https://supply-chain-network-design-gpsddgnqfkm2arhipwqjed.streamlit.app/

## ⚙️ Local Installation
```bash
git clone [https://github.com/ssharad922-a11y/supply-chain-network-design.git](https://github.com/ssharad922-a11y/supply-chain-network-design.git)
cd supply-chain-network-design
pip install -r requirements.txt
streamlit run app.py
