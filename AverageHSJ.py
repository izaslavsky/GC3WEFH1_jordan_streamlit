import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
import io

# Set Streamlit page
st.set_page_config(layout="wide")
st.title("Average Household Size of Jordan")

map_choice1 = st.selectbox("Choose a map", ["Please select a map type", "Average Household Size in Jordan States", "Average Household Size in Jordan"])
# Display other functionalities only if a map type is selected
if map_choice1 in ["Average Household Size in Jordan States", "Average Household Size in Jordan"]:
    # Function to read, clean, and merge data
    def prepare_data(csv_path, shp_path):
        csv_data = pd.read_csv(csv_path)
        shp_data = gpd.read_file(shp_path)
        csv_data['name'] = csv_data['name'].str.strip()  # Remove leading/trailing spaces
        shp_data['name'] = shp_data['name'].str.strip()
        merged_data = shp_data.merge(csv_data, on='name')
        id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
        return gpd.GeoDataFrame(merged_data, geometry='geometry'), id_name_df

    # Function to create Folium map and add GeoDataFrame
    def create_map(gdf, column_name):
        m = folium.Map(location=[31.95, 35.91], zoom_start=8)
        choropleth = folium.Choropleth(
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
        folium.GeoJson(gdf, name='geojson', tooltip=folium.features.GeoJsonTooltip(fields=['name', "TOTPOP_CY"])).add_to(m)
        return m

    # Generate gdf and ID name reference table
    if map_choice1 == "Average Household Size in Jordan States":
        gdf_jstates, id_name_df = prepare_data("dataset/Average Household Size in Jordan/governorate.csv", "jordan_admin_regions.shp")
        gdf = gdf_jstates
    elif map_choice1 == "Average Household Size in Jordan":
        gdf_jordan, id_name_df = prepare_data("dataset/Average Household Size in Jordan/country.csv", "jordan_admin_regions.shp")
        gdf = gdf_jordan

    # Layout columns
    col1, col2, col3 = st.columns([1, 5, 1])

    # Display ID and name reference table
    with col1:
        st.subheader("ID and Name Reference Table")
        st.dataframe(id_name_df, width=250)

    # Add filters
    with col2:
        selected_column = st.selectbox("Select a column to filter", gdf.columns[18:])
        filter_values = st.multiselect("Select values to keep", gdf[selected_column].unique())
        if filter_values:
            filtered_gdf = gdf[gdf[selected_column].isin(filter_values)].copy()
        else:
            filtered_gdf = gdf.copy()
        generate_map = st.button("Generate Map")
    
    with col3:
        param = pd.read_csv("dataset/Average Household Size in Jordan/para.csv")
        st.subheader("Parameter Reference Table")
        st.dataframe(param, width=250)

    # Display map when 'Generate Map' button is clicked
    if generate_map:
        with col2:
            if map_choice1 == "Average Household Size in Jordan States":
                map_to_display = create_map(filtered_gdf, selected_column)
            elif map_choice1 == "Average Household Size in Jordan":
                map_to_display = create_map(gdf_jordan, selected_column)
            folium_static(map_to_display, width=1087, height=600)
            st.subheader("Generated GeoDataFrame")
            filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
            filtered_gdf_slice = filtered_gdf.iloc[:, 18:]
            st.dataframe(filtered_gdf_slice, width=1300)

