import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
import io

# Set Streamlit page
st.set_page_config(layout="wide")
st.title("Healthcare Facilities in Jordan")

def load_data(csv_path):
    data = pd.read_csv(csv_path)
    return data

# Function to create map
def create_map(gdf, selected_column, tooltips):
    gdf = gpd.GeoDataFrame(gdf, geometry=gpd.points_from_xy(gdf.Longitude, gdf.Latitude))
    gdf.crs = "EPSG:4326"
    
    m = gdf.explore(
        column=selected_column,  
        cmap="Blues",
        scheme="FisherJenks",
        tiles="CartoDB dark_matter",
        tooltip=tooltips,
        popup=True,
        k=1,
        highlight=True,
        width="100%",
        legend_kwds={"caption": f"{selected_column} Statistics"},
        style_kwds={'radius': 8}
    )
    return m

# Main data loading
df = load_data("dataset/Healthcare Facilities in Jordan/healthcare.csv")

# Filter selector
filter_column = st.selectbox('Select a column to filter by:', df.columns)
filter_value_options = df[filter_column].unique().tolist()
filter_value_options.insert(0, "Choose a value")
selected_value = st.selectbox(f'Choose a value for {filter_column} filtering:', filter_value_options)
if selected_value != "Choose a value":
    df_filtered = df[df[filter_column] == selected_value]
else:
    df_filtered = df

st.subheader("Map Display:")
map_column = st.selectbox('Select a column to map:', df_filtered.columns)
tooltip_options = st.multiselect('Point Information:', df_filtered.columns)

map_gdf = create_map(df_filtered, map_column, tooltip_options)
folium_static(map_gdf, width=800, height=600)

# Display filtered data
st.subheader("Filtered Results:")
st.dataframe(df_filtered)