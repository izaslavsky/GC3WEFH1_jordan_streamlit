from pandasai.llm import GoogleGemini
import streamlit as st
import os
import pandas as pd
from pandasai import SmartDataframe
from pandasai.responses.response_parser import  ResponseParser
from fuzzywuzzy import fuzz
from streamlit.components.v1 import html
import requests
from pandas import json_normalize
import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
import io

# conda wen_streamlit_env - no map
# conda env map_wen_strmlit - with map

st.set_page_config(layout="wide")

if 'indicator_df' not in st.session_state:
    st.session_state.indicator_df = pd.read_csv('jordan_indicadors.csv', usecols=['GHO (CODE)', 'GHO (DISPLAY)'])

class StreamLitResponse(ResponseParser):
        def __init__(self,context) -> None:
              super().__init__(context)
        def format_dataframe(self,result):
               st.dataframe(result['value'])
               return
        def format_plot(self,result):
               st.image(result['value'])
               return
        def format_other(self, result):
               st.write(result['value'])
               return

gemini_api_key = os.environ['gemini']

def generateResponse(dataFrame,prompt):
        llm = GoogleGemini(api_key=gemini_api_key)
        pandas_agent = SmartDataframe(dataFrame,config={"llm":llm, "response_parser":StreamLitResponse, "custom_whitelisted_dependencies":["geopandas"]})
        answer = pandas_agent.chat(prompt)
        return answer

st.write("# Jordan Health Data")
# st.write("##### Engage in insightful conversations with your data through powerful visualizations, empowering you to uncover valuable insights and make informed decisions effortlessly!")

with st.sidebar:
        st.title("Map Steps")
        st.write('1. Choose a topic and a subsequent dataset to plot')
        st.write('2. Choose any filters and customize which columns are visible when hovering over the map.')
        st.write('4. Generate map and explore the data visually and in a dataset below')
        # st.divider()
        st.title("LLM Steps")
        st.write("Follow these steps to chat with the data:")
        st.write('1. Use the search bar to search for a WHO Indicator.')
        st.write('2. Choose the indicator you would like to interact with from the Results area.')
        st.write('3. If you only want to work with Jordan data, choose the "Show Jordan Data only" checkbox to apply filtering.')
        st.write('4. Explore your data in the data information dropdown')
        st.write('5. Ask your data questions!')

        st.write('### If it looks like your display is not loading, look at the top right corner of your browser and see if the LLM is running. ')

        # st.divider()

        # st.write('WHO Indicator List Steps:')
        # st.write('1. Search for "infectious disease"')
        # st.write('2. Choose the "Number of deaths attributed to non-communicable diseases, by type of disease and sex"')
        # st.write('3. Look through the Data information dropdown to see a preview of the data structure, a link to the data source, and a range of the values.')
        # st.write('4. Ask the tool: How many non-communicable diseases deaths were there in JOR?')
        # st.write('5. To see all the raw values for Jordan, Ask the tool: List all values for JOR in order of Time')
        # st.write('6. As you can tell, there are multiple values per year. To find the average value per year, ask the tool: List all average values for JOR in order of Time')
        # st.write('7. To chart the values over time, ask the tool: Graph all average deaths attributed to non-communicable diseases for JOR in order of Time')
        
        # st.write('Dataset List Steps:')s


map_label = r'''
$\textsf{
    \Large Map 
}$
'''

LLM_label = r'''
$\textsf{
    \Large LLM 
}$
'''

# col1, col2 = st.columns(2)
# tab1, tab2 = st.tabs(['Map', 'LLM'], )
tab1, tab2 = st.tabs([map_label, LLM_label])

with tab1:
    
    # Choose map type with dropdown
    col1, col2, col3 = st.columns(3)
    map_type_choice = col1.selectbox("Choose a Topic", ["", "Household", "Climate","Healthcare","Administrative"])
    if map_type_choice in ["Household"]:
        map_choice1 = col2.selectbox("Choose a Dataset", ["", "Jordan Population Average Statistics By State", "Jordan Population Average Statistics"])
        # Display other functionalities only if a map type is selected
        if map_choice1 in ["Jordan Population Average Statistics By State", "Jordan Population Average Statistics"]:
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
                folium.GeoJson(gdf, name='geojson', tooltip=folium.features.GeoJsonTooltip(fields=['name', column_name])).add_to(m)
                return m

            # Generate gdf and ID name reference table
            if map_choice1 == "Jordan Population Average Statistics By State":
                gdf_jstates, id_name_df = prepare_data("dataset/Average Household Size in Jordan/governorate.csv", "jordan_admin_regions.shp")
                gdf = gdf_jstates
            elif map_choice1 == "Jordan Population Average Statistics":
                gdf_jordan, id_name_df = prepare_data("dataset/Average Household Size in Jordan/country.csv", "jordan_admin_regions.shp")
                gdf = gdf_jordan

            # Layout columns
            household_col1, household_col2 = st.columns([1,2])

            # Display ID and name reference table
            # with col1:
            #     st.subheader("ID and Name Reference Table")
            #     st.dataframe(id_name_df, width=250)

            # Add filters
            with household_col1:
                param = pd.read_csv("dataset/Average Household Size in Jordan/para.csv")   
                descriptive_columns = param['Description']            
                selected_descriptive_column = st.selectbox("Select a Column to Display", descriptive_columns)
                selected_column = param[param['Description'] == selected_descriptive_column]['Parameter'].iloc[0].strip()
                generate_map = st.button("Generate Map")

            with household_col2:
                filter_values = st.multiselect("Filter Map by State", gdf['name'].unique(), default=gdf['name'].unique())
                if filter_values:
                    filtered_gdf = gdf[gdf['name'].isin(filter_values)].copy()
                else:
                    filtered_gdf = gdf.copy()

            # Display map when 'Generate Map' button is clicked
            if generate_map:
                with household_col1:
                    if map_choice1 == "Jordan Population Average Statistics By State":
                        map_to_display = create_map(filtered_gdf, selected_column)
                    elif map_choice1 == "Jordan Population Average Statistics":
                        map_to_display = create_map(gdf_jordan, selected_column)
                    # folium_static(map_to_display)
                    folium_static(map_to_display, width=1087, height=600)
            
            st.write("Data Displayed on Map:")
            filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
            filtered_column_gdf = filtered_gdf.iloc[:, 16:]
            renamed_columns = {}
            for x in param.iterrows():
                renamed_columns[x[1]['Parameter'].strip()] = x[1]['Description'].replace(' ', '_')

            renamed_columns['place_name'] = 'State'
            filtered_column_gdf = filtered_column_gdf.rename(columns=renamed_columns)
            st.dataframe(filtered_column_gdf)

    if map_type_choice in ["Climate"]:
        map_choice2 = col2.selectbox("Choose a Climate Dataset", ["Jordan Standardized Precipitation Index"])
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
            time_options.insert(0, 'All Data')
            selected_time = col3.selectbox('Select Timeframe to Plot:', time_options)

            # Filter data based on selected time
            if selected_time != 'All Data':
                df_filtered = df[df['Time'] == selected_time]
            else:
                df_filtered = df
            map_column = col3.selectbox('Select a column to map:', df_filtered.columns)
            tooltip_options = col3.multiselect('Point Information:', df_filtered.columns, default=list(df_filtered.columns))

            map_gdf = create_map(df_filtered, map_column, tooltip_options)
            with col1:
                st.write("")
                folium_static(map_gdf)
            # folium_static(map_gdf, width=800, height=600)
                
            # Display filtered data
            st.write("Data Displayed on Map:")
            st.dataframe(df_filtered)

            st.divider()

            # calc attributes can only be numeric, we need to filter out the non numeric values

            st.write('Summary Statistics')
            dtype_groups = df.columns.to_series().groupby(df.dtypes).groups
            numeric_columns = []
            dtype_dict = {k.name: v for k, v in dtype_groups.items() if k.name == 'int64' or k.name == 'float64'}

            if 'int64' in dtype_dict:
                for column in dtype_dict['int64']:
                    numeric_columns.append(column)
            if 'float64' in dtype_dict:
                for column in dtype_dict['float64']:
                    numeric_columns.append(column)

            col1_clim_cal, col2_clim_cal = st.columns(2)
            # Group and attribute selectors
            group_by_attribute = col1_clim_cal.selectbox('Group By Attribute:', df.columns)
            calc_attribute = col2_clim_cal.selectbox('Calculate Attribute:', numeric_columns)

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


    if map_type_choice in ["Healthcare"]:
        map_choice3 = col2.selectbox("Choose a Dataset", ["", "Healthcare Facilities in Jordan","Jordan Health","Jordan Health Map"])  
        if map_choice3 in ["Healthcare Facilities in Jordan"]:
            def load_data(csv_path):
                data = pd.read_csv(csv_path)
                return data

            # Function to create map
            def create_map(gdf, selected_column, tooltips):
                gdf = gpd.GeoDataFrame(gdf, geometry=gpd.points_from_xy(gdf.Longitude, gdf.Latitude))
                gdf.crs = "EPSG:4326"
                
                m = gdf.explore(
                    # column=selected_column,  
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

            facility_col1, facility_col2 = st.columns([1,1])

        # Filter selector
            # filter_column = facility_col1.selectbox('Select a Column to Display:', df.columns)
            # filter_value_options = df[filter_column].unique().tolist()
            # filter_value_options.insert(0, "Choose a value")
            filter_values = facility_col1.multiselect("Filter Map by Facility", df['Name_of_the_Facility'].unique(), default=df['Name_of_the_Facility'].unique())
            if filter_values:
                df_filtered = df[df['Name_of_the_Facility'].isin(filter_values)].copy()
            else:
                df_filtered = df.copy()

            tooltip_options = facility_col2.multiselect('Columns On Map:', df_filtered.columns, default=list(df_filtered.columns))

            map_gdf = create_map(df_filtered, 'Name', tooltip_options)
            folium_static(map_gdf, width=800, height=600)

            # Display filtered data
            st.write("Data Displayed in Map:")
            if len(tooltip_options) > 0:
                index_cols = [list(df_filtered.columns).index(x) for x in tooltip_options]
                df_filtered = df_filtered.iloc[:, index_cols]
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

            def create_map(gdf1, column_name, tooltip_options):
                gdf1.crs = "EPSG:4326"
                m = gdf1.explore(
                    column="Name", 
                    cmap="Blues",
                    scheme="FisherJenks",
                    tiles="CartoDB dark_matter",
                    tooltip=tooltip_options,
                    popup=True,
                    k=1,
                    highlight=True,
                    width="100%",
                    legend_kwds={"caption": f"{column_name} Statistics"},
                    style_kwds={'radius': 8}
                )
                
                return m

            gdf_jstates, id_name_df = prepare_data("dataset/Jordan Health/Governorates_jordan.csv", "jordan_admin_regions.shp")
            gdf = gdf_jstates

            df = pd.read_csv("dataset/Jordan Health/Hospitals.csv")
            gdf1 = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))

            print(df.columns)
            print(gdf1.columns)
           
            hospital_col1, hospital_col2 = st.columns([1,1])
            filter_values = hospital_col1.multiselect("Filter Map by Governorat", df['Governorat'].unique(), default=df['Governorat'].unique())
            if filter_values:
                df_filtered = df[df['Governorat'].isin(filter_values)].copy()
                gdf_filtered = gdf1[gdf1['Governorat'].isin(filter_values)].copy()
            else:
                df_filtered = df.copy()
                gdf_filtered = gdf1.copy()

            tooltip_options = hospital_col2.multiselect('Columns On Map:', df_filtered.columns, default=list(df_filtered.columns))

            generate_map = st.button("Generate Map")

            map_gdf = create_map(gdf_filtered, 'Governorat', tooltip_options)
            folium_static(map_gdf)

            # Display filtered data
            st.write("Data Displayed in Map:")
            if len(tooltip_options) > 0:
                index_cols = [list(df_filtered.columns).index(x) for x in tooltip_options]
                df_filtered = df_filtered.iloc[:, index_cols]
                st.dataframe(df_filtered)

        if map_choice3 in ["Jordan Health Map"]:
            def prepare_data(csv_path, shp_path):
                csv_data = pd.read_csv(csv_path)
                shp_data = gpd.read_file(shp_path)
                csv_data['name'] = csv_data['name'].str.strip()  # Remove leading/trailing spaces
                shp_data['name'] = shp_data['name'].str.strip()
                merged_data = shp_data.merge(csv_data, on='name')
                id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
                return gpd.GeoDataFrame(merged_data, geometry='geometry'), id_name_df

            def create_map(gdf1, column_name, tooltip_options):
                gdf1.crs = "EPSG:4326"
                m = gdf1.explore(
                    column="Activity", 
                    cmap="Blues",
                    scheme="FisherJenks",
                    tiles="CartoDB dark_matter",
                    tooltip=tooltip_options,
                    popup=True,
                    k=1,
                    highlight=True,
                    width="100%",
                    legend_kwds={"caption": f"{column_name} Statistics"},
                    style_kwds={'radius': 8}
                )
                
                return m

            gdf_jstates, id_name_df = prepare_data("dataset/Jordan Health/Governorates_jordan.csv", "jordan_admin_regions.shp")
            gdf = gdf_jstates

            df = pd.read_csv("dataset/Jordan Health Map/JCAP.csv")
            gdf1 = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))

            hospital_col1, hospital_col2 = st.columns([1,1])
            filter_values = hospital_col1.multiselect("Filter Map by Governorat", df['Governorat'].unique(), default=df['Governorat'].unique())
            if filter_values:
                df_filtered = df[df['Governorat'].isin(filter_values)].copy()
                gdf_filtered = gdf1[gdf1['Governorat'].isin(filter_values)].copy()
            else:
                df_filtered = df.copy()
                gdf_filtered = gdf1.copy()

            tooltip_options = hospital_col2.multiselect('Columns On Map:', df_filtered.columns, default=list(df_filtered.columns))

            generate_map = st.button("Generate Map")

            map_gdf = create_map(gdf_filtered, 'Governorat', tooltip_options)
            folium_static(map_gdf)

            # Display filtered data
            st.write("Data Displayed on Map:")
            if len(tooltip_options) > 0:
                index_cols = [list(df_filtered.columns).index(x) for x in tooltip_options]
                df_filtered = df_filtered.iloc[:, index_cols]
                st.dataframe(df_filtered)

    if map_type_choice in ["Administrative"]:

        map_choice1 = col2.selectbox("Choose a Dataset", ["Please select a map type", "Boundaries of Jordan States", "Boundaries of Jordan","Soviet"])
        # map_choice1 = col2.selectbox("Choose a Dataset", ["Please select a map type", "Boundaries of Jordan States", "Boundaries of Jordan","Soviet","Jordan Purchasing Power per Capita","Jordan Purchasing Power"])
        # Display other functionalities only if a map type is selected
        if map_choice1 in ["Boundaries of Jordan States", "Boundaries of Jordan"]:
            # Function to read, clean, and merge data
            def prepare_data(csv_path, shp_path):
                csv_data = pd.read_csv(csv_path)
                shp_data = gpd.read_file(shp_path)
                csv_data['name'] = csv_data['name'].str.strip()  # Remove leading/trailing spaces
                shp_data['name'] = shp_data['name'].str.strip()                
                merged_data = shp_data.merge(csv_data, on='name')
                # print(merged_data.columns)
                # id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
                return gpd.GeoDataFrame(merged_data, geometry='geometry')#, id_name_df

            # Function to create Folium map and add GeoDataFrame
            def create_map(gdf, tooltip_options):
                gdf.crs = "EPSG:4326"
                m = gdf.explore(
                    column="name", 
                    cmap="Blues",
                    scheme="FisherJenks",
                    tiles="CartoDB dark_matter",
                    tooltip=tooltip_options,
                    popup=True,
                    k=1,
                    highlight=True,
                    width="100%",
                    style_kwds={'radius': 8}
                )
                
                return m
                # m = folium.Map(location=[31.95, 35.91], zoom_start=8)
                # folium.Choropleth(
                #     geo_data=gdf,
                #     name='choropleth',
                #     # data=gdf,
                #     columns=['name', column_name],
                #     key_on='feature.properties.name',
                #     fill_color='YlGn',
                #     fill_opacity=0.7,
                #     line_opacity=0.2,
                #     legend_name='Legend Name',
                #     highlight=True,
                #     line_color='black',
                #     line_weight=1,
                #     tooltip=tooltip_options
                # ).add_to(m)
                # folium.GeoJson(gdf, name='geojson', tooltip=folium.features.GeoJsonTooltip(fields=tooltip_options)).add_to(m)
                # return m

            # Generate gdf and ID name reference table
            if map_choice1 in ["Boundaries of Jordan States"]:
                gdf_jstates = prepare_data("dataset/Jordan Boundaries/governorate.csv", "jordan_admin_regions.shp")
                # gdf_jstates, id_name_df = prepare_data("dataset/Jordan Boundaries/governorate.csv", "jordan_admin_regions.shp")
                gdf = gdf_jstates
            elif map_choice1 == "Boundaries of Jordan":
                gdf_jordan = prepare_data("dataset/Jordan Boundaries/country.csv", "jordan_admin_regions.shp")
                # gdf_jordan, id_name_df = prepare_data("dataset/Jordan Boundaries/country.csv", "jordan_admin_regions.shp")
                gdf = gdf_jordan

            boundary_col1, boundary_col2 = st.columns(2)

            boundary_col1, boundary_col2 = st.columns([1,1])
            filter_values = boundary_col1.multiselect("Filter Map by State", gdf['name'].unique(), default=gdf['name'].unique())
            if filter_values:
                # df_filtered = gdf[gdf['name'].isin(filter_values)].copy()
                gdf_filtered = gdf[gdf['name'].isin(filter_values)].copy()
            else:
                # df_filtered = df.copy()
                gdf_filtered = gdf1.copy()

            columns_not_geometry = [x for x in gdf_filtered.columns if x != 'geometry'][16:]
            tooltip_options = boundary_col2.multiselect('Columns On Map:', columns_not_geometry, default=list(columns_not_geometry))

            generate_map = st.button("Generate Map")

            print("tooltip_options")
            print(tooltip_options)

            map_gdf = create_map(gdf_filtered, tooltip_options)
            folium_static(map_gdf)

            # Display filtered data
            st.write("Data Displayed on Map:")
            if len(tooltip_options) > 0:
                index_cols = [list(gdf_filtered.columns).index(x) for x in tooltip_options]
                gdf_filtered = gdf_filtered.iloc[:, index_cols]
                df_filtered = pd.DataFrame(gdf_filtered)
                print(df_filtered)
                st.dataframe(df_filtered)

            # # Display ID and name reference table
            # with col1:
            #     st.subheader("ID and Name Reference Table")
            #     st.dataframe(id_name_df,width=250)

            # # Add filters
            # with col2:
            #     selected_column = st.selectbox("Select a column to filter", gdf.columns)
            #     filter_values = st.multiselect("Select values to keep", gdf[selected_column].unique())
            #     if filter_values:
            #         filtered_gdf = gdf[gdf[selected_column].isin(filter_values)].copy()
            #     else:
            #         filtered_gdf = gdf.copy()
            #     generate_map = st.button("Generate Map")

            # # Display map when 'Generate Map' button is clicked
            # if generate_map:
            #     with col2:
            #         if map_choice1 in ["Boundaries of Jordan States"]:
            #             map_to_display = create_map(filtered_gdf, selected_column)
            #         elif map_choice1 == "Boundaries of Jordan":
            #             map_to_display = create_map(gdf_jordan, selected_column)
            #         folium_static(map_to_display, width=800, height=600)
            #         st.subheader("Generated GeoDataFrame")
            #         filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
            #         filtered_gdf = filtered_gdf.iloc[:, 18:]
            #         st.dataframe(filtered_gdf, width=1300)

        # if map_choice1 in ["Jordan Purchasing Power per Capita","Jordan Purchasing Power"]:
        #     # Function to read, clean, and merge data
        #     def prepare_data(csv_path, shp_path):
        #         csv_data = pd.read_csv(csv_path)
        #         shp_data = gpd.read_file(shp_path)
        #         csv_data['name'] = csv_data['name'].str.strip()  # Remove leading/trailing spaces
        #         shp_data['name'] = shp_data['name'].str.strip()
        #         merged_data = shp_data.merge(csv_data, on='name')
        #         id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
        #         return gpd.GeoDataFrame(merged_data, geometry='geometry'), id_name_df

        #     # Function to create Folium map and add GeoDataFrame
        #     def create_map(gdf, column_name):
        #         m = folium.Map(location=[31.95, 35.91], zoom_start=8)
        #         folium.Choropleth(
        #             geo_data=gdf,
        #             name='choropleth',
        #             data=gdf,
        #             columns=['name', column_name],
        #             key_on='feature.properties.name',
        #             fill_color='YlGn',
        #             fill_opacity=0.7,
        #             line_opacity=0.2,
        #             legend_name='Legend Name',
        #             highlight=True,
        #             line_color='black',
        #             line_weight=1,
        #             tooltip=folium.features.GeoJsonTooltip(fields=['name', 'ID', column_name], labels=True, sticky=True)
        #         ).add_to(m)                
        #         folium.GeoJson(gdf, name='geojson', tooltip=folium.features.GeoJsonTooltip(fields=['place_name'])).add_to(m)
        #         return m

        #     # Generate gdf and ID name reference table
        #     if map_choice1 in ["Jordan Purchasing Power per Capita"]:
        #         gdf_jstates, id_name_df = prepare_data("dataset/Jordan Purchasing Power/governorate.csv", "jordan_admin_regions.shp")
        #         gdf = gdf_jstates
        #     elif map_choice1 == "Jordan Purchasing Power":
        #         gdf_jordan, id_name_df = prepare_data("dataset/Jordan Purchasing Power/country.csv", "jordan_admin_regions.shp")
        #         gdf = gdf_jordan

        #     # Layout columns
        #     col1, col2, col3 = st.columns([1, 5, 1])

        #     # Display ID and name reference table
        #     with col1:
        #         st.subheader("ID and Name Reference Table")
        #         st.dataframe(id_name_df)

        #     # Add filters
        #     with col2:
        #         selected_column = st.selectbox("Select a column to filter", gdf.columns)
        #         filter_values = st.multiselect("Select values to keep", gdf[selected_column].unique())
        #         if filter_values:
        #             filtered_gdf = gdf[gdf[selected_column].isin(filter_values)].copy()
        #         else:
        #             filtered_gdf = gdf.copy()
        #         generate_map = st.button("Generate Map")

        #     # Display map when 'Generate Map' button is clicked
        #     if generate_map:
        #         with col2:
        #             if map_choice1 in ["Jordan Purchasing Power per Capita"]:
        #                 map_to_display = create_map(filtered_gdf, selected_column)
        #             elif map_choice1 == "Jordan Purchasing Power":
        #                 map_to_display = create_map(gdf_jordan, selected_column)
        #             folium_static(map_to_display, width=800, height=600)
        #             st.write("Data Displayed on Map")
        #             filtered_gdf['geometry'] = filtered_gdf['geometry'].astype(str)
        #             filtered_gdf = filtered_gdf.iloc[:, 18:]
        #             st.dataframe(filtered_gdf, width=1300)

        #         with col3:
        #             param = pd.read_csv("dataset/Average Household Size in Jordan/para.csv")
        #             st.subheader("Parameter Reference Table")
        #             st.dataframe(param, width=250)    

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

    # # Function to load datasets from the "datasets" directory based on results.csv
    # def load_datasets_from_results_csv(results_csv_path):
    #     results_df = pd.read_csv(results_csv_path)
    #     datasets = [{'dataset_name': '- SELECT DATASET -', 'file_path': ''}]
    #     for _, row in results_df.iterrows():
    #         dataset_name = row['resource_name']
    #         file_path = os.path.join('datasets', row['file_name'])
    #         datasets.append({
    #             'dataset_name': dataset_name,
    #             'file_path': file_path
    #         })
    #     return pd.DataFrame(datasets)

    # # Load the datasets if not already in session state
    # if 'datasets_df' not in st.session_state:
    #     results_csv_path = 'dataset_name_list.csv'
    #     datasets_df = load_datasets_from_results_csv(results_csv_path)
    #     st.session_state.dropdown_list = datasets_df

    # loaded_selected_dataset = st.selectbox('Select From Datasets', datasets_df['dataset_name'])

    # if ('selected_dataset' not in st.session_state or \
    #     st.session_state.selected_dataset != loaded_selected_dataset) and loaded_selected_dataset != '- SELECT DATASET -':
    #     # Dropdown to select dataset
    #     st.session_state.selected_dataset = {
    #            'dataset_name' : loaded_selected_dataset,
    #            'dataset_type' : 'loaded',
    #            'file_path' : datasets_df.loc[datasets_df['dataset_name'] == loaded_selected_dataset].iloc[0]['file_path']
    #     }
    #     print(st.session_state.selected_dataset)

        # # Retrieve dataset information based on selected dataset
        # st.session_state.selected_dataset = {
        #         'dataset_name' : datasets_df.loc[datasets_df['dataset_name'] == st.session_state.selected_dataset].iloc[0],
        #         'dataset_type' : 'loaded'
        # }
        
        # # Reset WHO dataset 
        # st.session_state.selected_dataset_code = None

with tab2:
    
        # st.write('Dataset List Steps:')s
        
    # search datasets here
    search_input = st.text_input("Search WHO indicators") 

    who_selected_dataset = None

    if len(search_input) > 0 and ('search_input' not in st.session_state or \
        st.session_state.search_input != search_input):
        display_name_list = st.session_state.indicator_df['GHO (DISPLAY)']
        display_name_list = display_name_list.unique()
        display_name_list = [x for x in display_name_list if x != '#indicator+name' and x != 'nan']
        results = [[x, fuzz.token_set_ratio(search_input, x)] for x in display_name_list]    
        results.sort(key=lambda x: x[1], reverse=True)
        end_value = 15 if len(results) > 14 else len(results)
        st.session_state.search_results = [x[0] for x in results[:end_value]]

        if len(st.session_state.search_results) == 0:
            st.session_state.search_results = ['No results found']
        else:
            print('expander status: ', ('selected_dataset' in st.session_state and st.session_state.selected_dataset is not None) == False)
            with st.expander("Search Results: ", expanded=(('selected_dataset' in st.session_state and st.session_state.selected_dataset is not None) == False)):
                who_selected_dataset = st.radio('Choose an indicator to load:', st.session_state.search_results, index=None)


    if ('selected_dataset' not in st.session_state and who_selected_dataset is not None) or \
        ('selected_dataset' in st.session_state and st.session_state.selected_dataset != who_selected_dataset):

        print(who_selected_dataset)
        if who_selected_dataset is not None and len(who_selected_dataset) != 0:
            # Retrieve dataset information based on selected dataset
            dataset_code = st.session_state.indicator_df[st.session_state.indicator_df['GHO (DISPLAY)'] == who_selected_dataset]['GHO (CODE)'].iloc[0]
            # # Reset loaded_dataset 
            # st.session_state.loaded_datasets = None
            # print(st.session_state.selected_dataset_code)

            st.session_state.selected_dataset = {
                'dataset_name' : who_selected_dataset,
                'dataset_type' : 'WHO',
                'dataset_code' : dataset_code
            } 


    just_jordan_data = st.checkbox('Show Jordan Data only')

    if 'just_jordan_data' not in st.session_state or just_jordan_data != st.session_state.just_jordan_data:
         st.session_state.just_jordan_data = just_jordan_data


# uploaded_file = st.file_uploader("Upload your dataset here (CSV)",type="csv")
if 'selected_dataset' in st.session_state and st.session_state.selected_dataset is not None:
    if 'dataset_type' in st.session_state.selected_dataset and st.session_state.selected_dataset['dataset_type'] == 'WHO':
        # Read the CSV file
        url = 'https://ghoapi.azureedge.net/api/' + st.session_state.selected_dataset['dataset_code'] 

        if 'just_jordan_data' in st.session_state and st.session_state.just_jordan_data:
            print('just jordan')
            url = url + "?$filter=SpatialDim eq 'JOR'"

        print(url)
        response = requests.get(url)
        dictr = response.json()
        df = json_normalize(dictr['value'])
        
        is_numeric = any([x for x in df.NumericValue if x != None])
        # print('is numeric')
        # print(is_numeric)
        # unique_vals = df.Value.unique()        
        # unique_vals.sort()
        # range_str = ''  
        if is_numeric: 
            unique_vals = df.NumericValue.unique()        
            unique_vals.sort()
            range_str = str(unique_vals[0]) + ' - ' + str(unique_vals[-1])
            df['Value'] = df['NumericValue']
            df = df.astype({'Value': 'float', 'TimeDimensionValue' : 'int', 'SpatialDimType' : 'str', 'SpatialDim' : 'str'})
        else:
            unique_vals = df.Value.unique()        
            unique_vals.sort()
            if len(df.values) < 30:
                range_str = ', '.join(unique_vals)
            else:
                 range_str = None
        
        print(df.columns)
        parsed_df = df[['Id', 'SpatialDimType', 'SpatialDim', 'TimeDimensionValue', 'Value']]
        parsed_df = parsed_df.rename(columns={'SpatialDimType' : 'Spatial_Scope', 'SpatialDim' : "Spatial_Entity",\
                                               'TimeDimensionValue' : "Time", \
                                               'Value' : 'value'
                                                #'Value' : '_'.join(st.session_state.selected_dataset.split(' '))
                                                })

        st.session_state.df = parsed_df

    else:
      
        # Read the CSV file
        print('here here ')
        df = pd.read_csv(st.session_state.selected_dataset['file_path'])
        print('did it get it')
        print(len(df))

        # st.session_state.selected_dataset = st.session_state.selected_dataset['dataset_name']

        st.session_state.df = df
        st.session_state.dataset_type = 'loaded'
        # Display the data
        # with st.expander("Preview"):
        #     st.write(df.head())

        # # Plot the data
        # user_input = st.text_input("Type your message here",placeholder="Ask me about your data")
        # if user_input:
        #         answer = generateResponse(dataFrame=df,prompt=user_input)
        #         st.write(answer)

# Display the data

if 'df' in st.session_state and 'selected_dataset' in st.session_state:
    preview_txt = 'Data Information'
    if 'dataset_type' in st.session_state and st.session_state.dataset_type == 'WHO':
        preview_txt = "Dataset Information"


    with st.expander(preview_txt):
        st.write('Preview of ' + st.session_state.selected_dataset['dataset_name'])
        st.write(st.session_state.df.head())

        if st.session_state.selected_dataset['dataset_type'] == 'WHO':
            st.write("Indicator Information")
            st.write("https://www.who.int/data/gho/data/indicators/indicator-details/GHO/" + st.session_state.selected_dataset['dataset_name'].replace(' ', '-'))

            st.write('Range of Values')
            if range_str == None:
                st.write('Too many values to list, use the chat interface for more details on the values.')
            else:
                 st.write(range_str)

if 'df' in st.session_state and st.session_state.df is not None:
    
    st.write(st.session_state.selected_dataset['dataset_name'])
    schema_definitions = None
    if st.session_state.selected_dataset['dataset_type'] == 'loaded' and \
        (st.session_state.selected_dataset['dataset_name'] == 'country' or st.session_state.selected_dataset['dataset_name'] == 'governorate'):
         country_schema = pd.read_csv('datasets/country_schema.csv')
         schema_definitions = 'Here is a list of all the definitions per column: '
         for x in country_schema.iterrows():
              schema_definitions += 'The column ' + x[1]['column_name'] + ' means ' + x[1]['column_definition'] + '.' +\
                ' If a user asks about topics related to ' + x[1]['column_definition'] + ', use column ' +  x[1]['column_name'] + '.'
         

    # Plot the data
    user_input = st.text_input("Type your message here",placeholder="Ask me about your data")
    if user_input:
            prompt_input = 'The SpatialDim has the country alpha-3 codes. The value' + \
            ' column means ' + st.session_state.selected_dataset['dataset_name'] + ' If you are unsure which column to use as the data, use value. ' + \
            'If you create a graph using the Time column, make sure the values are in order.' + \
            (schema_definitions if schema_definitions != None else '') + \
            'If you receive an error, please print the error in full. Here is the user input : ' + user_input
            print(prompt_input)
            answer = generateResponse(dataFrame=st.session_state.df,prompt=prompt_input)
            st.write(answer)
            # 'If the user wants to map a dataset, use the geopandas function explore. Here is an example: geopandas.explore(df)' + \


