import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
import io

# Set Streamlit page
st.set_page_config(layout="wide")
start_choice = st.selectbox("Overview or Start?", ["Overview", "Start!"])

if start_choice == "Overview":
    st.markdown("## What can we do with these maps?")
    st.markdown("* 1. View dataframe of jordan")
    st.markdown("* 2. Visualize data on a map")
    st.markdown("* 3. Filter data based on certain attributes and visualize it on a map")
    st.markdown("* 4. Download (filtered) dataset")

    st.title('Jordan Public Datasets')
    type_choice = st.selectbox("Choose a map", ["Please select a map type", "Household", "Climate","Healthcare","Administrative"])
    if type_choice in ["Household"]:
        st.image("overview/Average Household Size in Jordan.png", use_column_width=True)
    if type_choice in ["Climate"]:
        st.markdown("## Jordan SPI")
        st.image("overview/spi.png", use_column_width=True)
    if type_choice in ["Healthcare"]:
        st.image("overview/Health_jordan.png", use_column_width=True)
        st.image("overview/Healthcare Facilities in Jordan.png", use_column_width=True)
        st.image("overview/jordan health activities.png", use_column_width=True)
        st.image("overview/Jordan Health EPE.png", use_column_width=True)
        st.image("overview/Jordan Health.png", use_column_width=True)
    if type_choice in ["Administrative"]:
        st.image("overview/Jordan Boundaries.png", use_column_width=True)
        st.image("overview/Jordan Purchasing Power.png", use_column_width=True)
        st.image("overview/jordan soviet.png", use_column_width=True)

if start_choice == "Start!":
    st.title("Map Visualization")
# Choose map type with dropdown
    map_type_choice = st.selectbox("Choose a type", ["Please select a map type", "Household", "Climate","Healthcare","Administrative"])
    if map_type_choice in ["Household"]:
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
                    st.dataframe(filtered_gdf, width=1300)

    if map_type_choice in ["Climate"]:
        map_choice2 = st.selectbox("Choose a map", ["Please select a map type", "Jordan Standardized Precipitation Index"])
    # Choose map type with dropdown
        if map_choice2 in ["Jordan Standardized Precipitation Index"]:
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
                    k=6,
                    highlight=True,
                    width="100%",
                    legend_kwds={"caption": f"{selected_column} Statistics"},
                    style_kwds={'radius': 8}
                )
                return m

            # Main data loading
            df = load_data("170/SPI_JMD_data_corrected_long_format.csv")

            # Time selector
            time_options = list(df['Time'].unique())
            time_options.insert(0, 'all')
            selected_time = st.selectbox('Select Time:', time_options)

            # Filter data based on selected time
            if selected_time != 'all':
                df_filtered = df[df['Time'] == selected_time]
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

            # Group and attribute selectors
            group_by_attribute = st.selectbox('Group By Attribute:', df.columns)
            calc_attribute = st.selectbox('Calculate Attribute:', df.columns)

            # Calculate statistics
            if st.button('Calculate Statistics'):
                aggregation_functions = {
                    calc_attribute: ['max', 'min', 'mean'],
                    'Latitude': 'first',
                    'Longitude': 'first'
                }
                grouped_df = df.groupby(group_by_attribute).agg(aggregation_functions).reset_index()
                grouped_df.columns = [col[0] if col[-1] == '' or col[-1] == 'first' else '_'.join(col) for col in grouped_df.columns.values]
                st.dataframe(grouped_df)

                # Map related selectors
                map_column = st.selectbox('Select a column to map:', grouped_df.columns)
                tooltip_options = st.multiselect('Point Information:', grouped_df.columns)

    if map_type_choice in ["Healthcare"]:
        map_choice3 = st.selectbox("Choose a map", ["Please select a map type", "Healthcare Facilities in Jordan","Jordan Health","Jordan Health Map"])  
        if map_choice3 in ["Healthcare Facilities in Jordan"]:
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
        
        if map_choice3 in ["Jordan Health"]:
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
                    st.dataframe(filtered_gdf, width=1300)
                    filtered_gdf1['geometry'] = filtered_gdf1['geometry'].astype(str)
                    st.dataframe(filtered_gdf1, width=1300)
            
        if map_choice3 in ["Jordan Health Map"]:
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
                    column="ID", 
                    cmap="Blues", 
                    scheme="FisherJenks", 
                    tiles="CartoDB dark_matter", 
                    tooltip=["SectorType", "Benefiting", "Governorat"], 
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
                folium.LayerControl().add_to(m)  
                return m

            gdf_jstates, id_name_df = prepare_data("dataset/Jordan Health Map/Governorates_jordan.csv", "jordan_admin_regions.shp")
            gdf = gdf_jstates

            df = pd.read_csv("dataset/Jordan Health Map/JCAP.csv")
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
            if generate_map:
                with col2:
                    map_to_display = create_map(filtered_gdf1,filtered_gdf, selected_column)
                    folium_static(map_to_display, width=800, height=600)
                    st.subheader("Generated GeoDataFrame")
                    filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
                    filtered_gdf = filtered_gdf.iloc[:, 18:]
                    st.dataframe(filtered_gdf, width=1300)
                    filtered_gdf1['geometry'] = filtered_gdf1['geometry'].astype(str)
                    st.dataframe(filtered_gdf1, width=1300)

    if map_type_choice in ["Administrative"]:
        map_choice1 = st.selectbox("Choose a map", ["Please select a map type", "Boundaries of Jordan States", "Boundaries of Jordan","Soviet","Jordan Purchasing Power per Capita","Jordan Purchasing Power"])
        # Display other functionalities only if a map type is selected
        if map_choice1 in ["Boundaries of Jordan States", "Boundaries of Jordan"]:
            # Function to read, clean, and merge data
            def prepare_data(csv_path, shp_path):
                csv_data = pd.read_csv(csv_path)
                shp_data = gpd.read_file(shp_path)
                csv_data['name'] = csv_data['name'].str.strip()  # Remove leading/trailing spaces
                shp_data['name'] = shp_data['name'].str.strip()
                merged_data = shp_data.merge(csv_data, on='ID')
                id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
                return gpd.GeoDataFrame(merged_data, geometry='geometry'), id_name_df

            # Function to create Folium map and add GeoDataFrame
            def create_map(gdf, column_name):
                m = folium.Map(location=[31.95, 35.91], zoom_start=8)
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
                return m

            # Generate gdf and ID name reference table
            if map_choice1 in ["Boundaries of Jordan States"]:
                gdf_jstates, id_name_df = prepare_data("dataset/Jordan Boundaries/governorate.csv", "jordan_admin_regions.shp")
                gdf = gdf_jstates
            elif map_choice1 == "Boundaries of Jordan":
                gdf_jordan, id_name_df = prepare_data("dataset/Jordan Boundaries/country.csv", "jordan_admin_regions.shp")
                gdf = gdf_jordan

            # Layout columns
            col1, col2, col3 = st.columns([1, 5, 1])

            # Display ID and name reference table
            with col1:
                st.subheader("ID and Name Reference Table")
                st.dataframe(id_name_df,width=250)

            # Add filters
            with col2:
                selected_column = st.selectbox("Select a column to filter", gdf.columns)
                filter_values = st.multiselect("Select values to keep", gdf[selected_column].unique())
                if filter_values:
                    filtered_gdf = gdf[gdf[selected_column].isin(filter_values)].copy()
                else:
                    filtered_gdf = gdf.copy()
                generate_map = st.button("Generate Map")

            # Display map when 'Generate Map' button is clicked
            if generate_map:
                with col2:
                    if map_choice1 in ["Boundaries of Jordan States"]:
                        map_to_display = create_map(filtered_gdf, selected_column)
                    elif map_choice1 == "Boundaries of Jordan":
                        map_to_display = create_map(gdf_jordan, selected_column)
                    folium_static(map_to_display, width=800, height=600)
                    st.subheader("Generated GeoDataFrame")
                    filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
                    filtered_gdf = filtered_gdf.iloc[:, 18:]
                    st.dataframe(filtered_gdf, width=1300)

        if map_choice1 in ["Jordan Purchasing Power per Capita","Jordan Purchasing Power"]:
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
                return m

            # Generate gdf and ID name reference table
            if map_choice1 in ["Jordan Purchasing Power per Capita"]:
                gdf_jstates, id_name_df = prepare_data("dataset/Jordan Purchasing Power/governorate.csv", "jordan_admin_regions.shp")
                gdf = gdf_jstates
            elif map_choice1 == "Jordan Purchasing Power":
                gdf_jordan, id_name_df = prepare_data("dataset/Jordan Purchasing Power/country.csv", "jordan_admin_regions.shp")
                gdf = gdf_jordan

            # Layout columns
            col1, col2, col3 = st.columns([1, 5, 1])

            # Display ID and name reference table
            with col1:
                st.subheader("ID and Name Reference Table")
                st.dataframe(id_name_df)

            # Add filters
            with col2:
                selected_column = st.selectbox("Select a column to filter", gdf.columns)
                filter_values = st.multiselect("Select values to keep", gdf[selected_column].unique())
                if filter_values:
                    filtered_gdf = gdf[gdf[selected_column].isin(filter_values)].copy()
                else:
                    filtered_gdf = gdf.copy()
                generate_map = st.button("Generate Map")

            # Display map when 'Generate Map' button is clicked
            if generate_map:
                with col2:
                    if map_choice1 in ["Jordan Purchasing Power per Capita"]:
                        map_to_display = create_map(filtered_gdf, selected_column)
                    elif map_choice1 == "Jordan Purchasing Power":
                        map_to_display = create_map(gdf_jordan, selected_column)
                    folium_static(map_to_display, width=800, height=600)
                    st.subheader("Generated GeoDataFrame")
                    filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
                    filtered_gdf = filtered_gdf.iloc[:, 18:]
                    st.dataframe(filtered_gdf, width=1300)

                with col3:
                    param = pd.read_csv("dataset/Average Household Size in Jordan/para.csv")
                    st.subheader("Parameter Reference Table")
                    st.dataframe(param, width=250)    

        if map_choice1 in ["Soviet"]:

            gdf = gpd.read_file("dataset/Soviet/layer_0.shp")
            generate_map = st.button("Generate Map")
            if generate_map:
                with st.spinner("Generating map..."):
                    m = gdf.explore()
                    folium_static(m, width=800, height=600)
                    st.subheader("Generated GeoDataFrame")
                    gdf['geometry'] = gdf['geometry'].astype(str)
                    st.dataframe(gdf, width=1300)