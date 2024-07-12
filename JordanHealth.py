import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
import io

# Set Streamlit page
st.set_page_config(layout="wide")
st.title("Jordan Health")

def prepare_data(csv_path, shp_path):
    csv_data = pd.read_csv(csv_path)
    shp_data = gpd.read_file(shp_path)
    csv_data['name'] = csv_data['name'].str.strip()  # Remove leading/trailing spaces
    shp_data['name'] = shp_data['name'].str.strip()
    merged_data = shp_data.merge(csv_data, on='name')
    id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
    return gpd.GeoDataFrame(merged_data, geometry='geometry'), id_name_df

def create_map(gdf1,gdf, column_name):
    gdf1.crs = "EPSG:4326"
    m = gdf1.explore(
        column="Name", 
        cmap="Blues", 
        scheme="FisherJenks", 
        tiles="CartoDB dark_matter", 
        tooltip=["Governorat", "Type", "Number_bed"], 
        popup=True,
        highlight=True,
        width="50%", 
        style_kwds={'radius': 8}
    )
    folium.Choropleth(
        geo_data=gdf,
        name='choropleth',
        data=gdf,
        columns=['name', column_name],
        key_on='feature.properties.name',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Legend Name',
        highlight=True,
        line_color='black',
        line_weight=1,
        tooltip=folium.features.GeoJsonTooltip(fields=['name', 'ID', column_name], labels=True, sticky=True)
    ).add_to(m)
    folium.GeoJson(gdf, name='geojson', tooltip=folium.features.GeoJsonTooltip(fields=['name'])).add_to(m)
    folium.LayerControl().add_to(m)  # 添加图层控制
    return m

gdf_jstates, id_name_df = prepare_data("dataset/Jordan Health/Governorates_jordan.csv", "jordan_admin_regions.shp")
gdf = gdf_jstates

df = pd.read_csv("dataset/Jordan Health/Hospitals.csv")
gdf1 = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))

# Layout columns
col1, col2, col3 = st.columns([1, 5, 1])

# Display ID and name reference table
with col1:
    st.subheader("ID and Name Reference Table")
    st.dataframe(id_name_df, width=250)

# Add filters
with col2:
    selected_column = st.selectbox("Select a column to filter", gdf.columns)
    filter_values = st.multiselect("Select values to keep", gdf[selected_column].unique())
    if filter_values:
        filtered_gdf = gdf[gdf[selected_column].isin(filter_values)].copy()
    else:
        filtered_gdf = gdf.copy()

    selected_column1 = st.selectbox("Select a column to filter", gdf1.columns)
    filter_values1 = st.multiselect("Select values to keep", gdf1[selected_column1].unique())
    if filter_values1:
        filtered_gdf1 = gdf1[gdf1[selected_column1].isin(filter_values1)].copy()
    else:
        filtered_gdf1 = gdf1.copy()

    generate_map = st.button("Generate Map")

# Display map when 'Generate Map' button is clicked
if generate_map:
    with col2:
        map_to_display = create_map(filtered_gdf1,filtered_gdf, selected_column)
        folium_static(map_to_display, width=1087, height=600)
        st.subheader("Generated GeoDataFrame")
        filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
        filtered_gdf_slice = filtered_gdf.iloc[:, 18:]
        st.dataframe(filtered_gdf_slice, width=1300)
        filtered_gdf1['geometry'] = filtered_gdf1['geometry'].astype(str)
        st.dataframe(filtered_gdf1, width=1300)