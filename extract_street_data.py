import geopandas as gpd
import folium
from shapely.geometry import Point, LineString, MultiLineString
import os
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import webbrowser
import tempfile
from geopy.geocoders import Nominatim
import json
from datetime import datetime
import svgwrite
from svgwrite import cm, mm
from shapely.ops import transform
import pyproj
import numpy as np
from shapely.affinity import scale, translate

# Get the absolute path of the current working directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Miles to meters conversion factor
MILES_TO_METERS = 1609.34

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def extract_street_data(address, radius_miles, data_type='traffic'):
    """
    Extract street data within a specified radius of a given address.
    
    Args:
    address (str): Address in New York City
    radius_miles (float): Search radius (miles)
    data_type (str): 'traffic' or 'pedestrian'
    
    Returns:
    GeoDataFrame: Filtered street data
    """
    # Convert miles to meters
    radius_meters = radius_miles * MILES_TO_METERS
    
    # Select data source based on type
    if data_type == 'traffic':
        data_path = os.path.join(BASE_DIR, 'Centerline_20250522', 'geo_export_afeb978c-bd19-430e-9999-6417824a9aae.shp')
    else:
        data_path = os.path.join(BASE_DIR, 'NYC Planimetric Database_ Sidewalk_20250523v2', 'geo_export_e1ca140e-1b37-4130-a4f9-9d5ed9ff9446.shp')
    
    print(f"Reading data file: {data_path}")
    
    # Check if file exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Read data
    gdf = gpd.read_file(data_path)
    
    # Geocode address
    geolocator = Nominatim(user_agent="nyc_street_extractor")
    for i in range(3):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location is not None:
                break
        except Exception as e:
            print(f'Geocoding attempt {i+1} failed, retrying... Error: {e}')
            location = None
    if location is None:
        raise ValueError(f"Could not find address: {address}")
    
    print(f"Address coordinates: lon={location.longitude}, lat={location.latitude}")
    point = Point(location.longitude, location.latitude)
    print("gdf crs:", gdf.crs)
    print("point:", point)

    # Buffer based on CRS
    if gdf.crs and gdf.crs.is_geographic:
        # Geographic coordinates
        buffer = point.buffer(radius_meters / 111000)
    else:
        # Projected coordinates, transform point to gdf CRS
        project = pyproj.Transformer.from_crs("EPSG:4326", gdf.crs, always_xy=True).transform
        point_proj = transform(project, point)
        buffer = point_proj.buffer(radius_meters)

    print("buffer.bounds:", buffer.bounds)
    result = gdf[gdf.geometry.intersects(buffer)]
    print("Original gdf count:", len(gdf))
    print("Filtered count:", len(result))
    print(result.geometry.type.value_counts())
    return result

def export_to_html(gdf, output_path):
    """
    Export GeoDataFrame to interactive HTML map
    """
    # Convert all Timestamp columns to string
    for col in gdf.columns:
        if gdf[col].dtype.name.startswith('datetime') or gdf[col].dtype.name == 'object':
            gdf[col] = gdf[col].astype(str)

    # Create map
    m = folium.Map(location=[40.7128, -74.0060], zoom_start=13)
    
    # Convert GeoDataFrame to GeoJSON
    geojson_data = json.loads(gdf.to_json())
    
    # Add GeoJSON data
    folium.GeoJson(
        geojson_data,
        name='Street Data',
        style_function=lambda x: {'color': 'blue', 'weight': 2}
    ).add_to(m)
    
    # Save map
    m.save(output_path)
    
    # Open in browser
    webbrowser.open('file://' + os.path.abspath(output_path))

def shrink_polygon(geom, factor):
    # factor < 1 会缩小
    centroid = geom.centroid
    return scale(geom, xfact=factor, yfact=factor, origin=centroid)

def export_to_svg(gdf, output_path, data_type='traffic'):
    """
    Export GeoDataFrame to SVG file. Supports LineString, MultiLineString, Polygon, MultiPolygon.
    Optimized: no background, line width 1 for traffic, line width 2 for sidewalk, only draw Polygon exterior.
    For pedestrian data, increases spacing between blocks by shifting each block away from the global centroid.
    
    Args:
        gdf (GeoDataFrame): Input GeoDataFrame
        output_path (str): Output SVG file path
        data_type (str): 'traffic' or 'pedestrian'
    """
    try:
        from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon
        from shapely.affinity import translate
        import numpy as np

        # Fixed canvas size
        svg_width = 1000
        svg_height = 1000
        margin = 40  # margin in pixels

        # Set line width based on data type
        line_width = 2 if data_type == 'pedestrian' else 1

        # Only keep valid geometry types
        gdf = gdf[gdf.geometry.type.isin(['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon'])]
        if gdf.empty:
            print("No valid line or polygon data, cannot generate SVG.")
            return

        # Get bounding box
        bounds = gdf.total_bounds
        minx, miny, maxx, maxy = bounds
        width = maxx - minx
        height = maxy - miny

        # Prevent division by zero
        if width == 0 or height == 0:
            print("Data range too small, cannot generate valid SVG.")
            return

        # Calculate scale with margin
        scale_x = (svg_width - 2 * margin) / width
        scale_y = (svg_height - 2 * margin) / height
        scale = min(scale_x, scale_y)

        # For pedestrian data, increase spacing between blocks by shifting
        if data_type == 'pedestrian':
            centroids = [geom.centroid for geom in gdf.geometry]
            global_cx = np.mean([c.x for c in centroids])
            global_cy = np.mean([c.y for c in centroids])
            move_ratio = 0.2  # 0.2表示间距增加20%，可根据需要调整

            new_geometries = []
            for geom, centroid in zip(gdf.geometry, centroids):
                dx = centroid.x - global_cx
                dy = centroid.y - global_cy
                new_geom = translate(geom, xoff=dx * move_ratio, yoff=dy * move_ratio)
                new_geometries.append(new_geom)
            gdf = gdf.copy()
            gdf.geometry = new_geometries
            # 重新计算bounds和scale
            bounds = gdf.total_bounds
            minx, miny, maxx, maxy = bounds
            width = maxx - minx
            height = maxy - miny
            scale_x = (svg_width - 2 * margin) / width
            scale_y = (svg_height - 2 * margin) / height
            scale = min(scale_x, scale_y)

        def transform_coords(x, y):
            svg_x = (x - minx) * scale + margin
            svg_y = (maxy - y) * scale + margin  # Flip Y axis
            return svg_x, svg_y

        import svgwrite
        dwg = svgwrite.Drawing(output_path, size=(svg_width, svg_height))
        # No background

        # Draw all types
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if isinstance(geom, LineString):
                coords = [transform_coords(x, y) for x, y in geom.coords]
                if len(coords) > 1:
                    dwg.add(dwg.polyline(coords, stroke='blue', stroke_width=line_width, fill='none'))
            elif isinstance(geom, MultiLineString):
                for line in geom.geoms:
                    coords = [transform_coords(x, y) for x, y in line.coords]
                    if len(coords) > 1:
                        dwg.add(dwg.polyline(coords, stroke='blue', stroke_width=line_width, fill='none'))
            elif isinstance(geom, Polygon):
                exterior = [transform_coords(x, y) for x, y in geom.exterior.coords]
                dwg.add(dwg.polyline(exterior, stroke='blue', stroke_width=line_width, fill='none'))
                # Do not draw interior
            elif isinstance(geom, MultiPolygon):
                for poly in geom.geoms:
                    exterior = [transform_coords(x, y) for x, y in poly.exterior.coords]
                    dwg.add(dwg.polyline(exterior, stroke='blue', stroke_width=line_width, fill='none'))
                    # Do not draw interior

        dwg.save()
        print(f"SVG file generated: {output_path}")

    except Exception as e:
        print(f"Warning: Error generating SVG file: {str(e)}")
        print("Will use HTML format instead.")
        html_path = output_path.replace('.svg', '.html')
        export_to_html(gdf, html_path)

def get_user_input():
    """
    Get user input
    """
    print("\n=== NYC Street Data Extraction Tool ===")
    print("Please enter the following information:")
    
    # Get address
    while True:
        address = input("\nEnter New York City address (e.g. 350 5th Ave, New York, NY 10118): ").strip()
        if address:
            break
        print("Address cannot be empty, please re-enter!")
    
    # Get radius (miles)
    while True:
        try:
            radius = float(input("\nEnter search radius (miles): ").strip())
            if radius > 0:
                break
            print("Radius must be greater than 0, please re-enter!")
        except ValueError:
            print("Please enter a valid number!")
    
    # Get data type
    while True:
        data_type = input("\nSelect data type (1: Centerline, 2: Sidewalk): ").strip()
        if data_type in ['1', '2']:
            data_type = 'traffic' if data_type == '1' else 'pedestrian'
            break
        print("Please enter 1 or 2!")
    
    # Get output format
    while True:
        output_format = input("\nSelect output format (1: HTML map, 2: SVG file, 3: Both): ").strip()
        if output_format in ['1', '2', '3']:
            break
        print("Please enter 1, 2, or 3!")

    # Get export path
    export_path = input("\nEnter export file base name or path (leave blank for default): ").strip()
    if not export_path:
        export_path = None
    
    return address, radius, data_type, output_format, export_path

def main():
    """
    Main function
    """
    while True:
        try:
            # Get user input
            address, radius_miles, data_type, output_format, export_path = get_user_input()
            
            # Extract data
            data = extract_street_data(address, radius_miles, data_type)
            
            if data.empty:
                print(f"No {data_type} data found within {radius_miles} miles of {address}")
            else:
                print(f"\nFound {len(data)} {data_type} features")
                
                # 判断导出路径是文件夹还是文件名
                if export_path and os.path.isdir(export_path):
                    html_path = os.path.join(export_path, f"{data_type}_map.html")
                    svg_path = os.path.join(export_path, f"{data_type}_map.svg")
                else:
                    html_path = export_path if (export_path and export_path.endswith('.html')) else (export_path + '_map.html' if export_path else f"{data_type}_map.html")
                    svg_path = export_path if (export_path and export_path.endswith('.svg')) else (export_path + '_map.svg' if export_path else f"{data_type}_map.svg")
                
                # Export based on output format
                if output_format in ['1', '3']:
                    print(f"\nGenerating HTML file: {html_path}")
                    export_to_html(data, html_path)
                
                if output_format in ['2', '3']:
                    print(f"\nGenerating SVG file: {svg_path}")
                    export_to_svg(data, svg_path, data_type)
            
            # Ask if continue
            if input("\nDo you want to search another location? (y/n): ").lower() != 'y':
                break
                
        except Exception as e:
            print(f"Error: {str(e)}")
            if input("\nDo you want to try again? (y/n): ").lower() != 'y':
                break

if __name__ == "__main__":
    main() 