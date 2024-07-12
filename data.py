import pandas as pd
import geopandas as gpd

def prepare_data(csv_path, shp_path):
    csv_data = pd.read_csv(csv_path)
    shp_data = gpd.read_file(shp_path)
    csv_data['name'] = csv_data['name'].str.strip()
    shp_data['name'] = shp_data['name'].str.strip()
    merged_data = shp_data.merge(csv_data, on='name')
    id_name_df = pd.DataFrame({'ID': merged_data['ID'], 'name': merged_data['name']})
    return gpd.GeoDataFrame(merged_data, geometry='geometry'), id_name_df

gdf_jstates, id_name_df1 = prepare_data("dataset/Jordan Purchasing Power/governorate.csv", "jordan_admin_regions.shp")
gdf_jordan, id_name_df2 = prepare_data("dataset/Jordan Purchasing Power/country.csv", "jordan_admin_regions.shp")

shp_data = gpd.read_file("jordan_admin_regions.shp")
gdf= gpd.GeoDataFrame(shp_data, geometry='geometry')
output_file = "dataset/jordan_admin_regions.geojson"
## gdf_jstates = gdf_jstates.drop(gdf_jstates.columns[:17], axis=1)
gdf.to_file(output_file, driver="GeoJSON")