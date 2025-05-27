# NYC Street Data Extraction Tool

A Python tool for extracting and visualizing street centerlines and sidewalk data from New York City addresses within a specified radius. This tool is particularly useful for urban planning, transportation analysis, and pedestrian accessibility studies.

## Features

- Extract street centerlines and sidewalk data from NYC addresses
- Support for both traffic (centerline) and pedestrian (sidewalk) data
- Interactive HTML map export with Folium
- SVG file export with optimized visualization
- Automatic geocoding of addresses
- Configurable search radius
- Support for multiple output formats
- Automatic coordinate system transformation
- Optimized visualization for both traffic and pedestrian data

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.8 or higher
- Required Python packages:
  - geopandas>=0.10.0
  - folium>=0.12.0
  - shapely>=1.8.0
  - svglib>=1.5.0
  - reportlab>=3.6.0
  - geopy>=2.2.0
  - svgwrite>=1.4.0
  - pyproj>=3.0.0
  - numpy>=1.20.0

## Data Sources

The tool uses two main data sources:
1. NYC Centerline Data (traffic)
   - Location: `Centerline_20250522/geo_export_afeb978c-bd19-430e-9999-6417824a9aae.shp`
   - Contains street centerlines for traffic analysis
2. NYC Planimetric Database Sidewalk Data (pedestrian)
   - Location: `NYC Planimetric Database_ Sidewalk_20250523v2/geo_export_e1ca140e-1b37-4130-a4f9-9d5ed9ff9446.shp`
   - Contains detailed sidewalk information

## Usage

1. Run the script:
```bash
python extract_street_data.py
```

2. Follow the interactive prompts:
   - Enter a New York City address (e.g., "350 5th Ave, New York, NY 10118")
   - Specify the search radius in miles (e.g., 0.5)
   - Choose data type:
     - 1: Centerline (traffic data)
     - 2: Sidewalk (pedestrian data)
   - Select output format:
     - 1: HTML map
     - 2: SVG file
     - 3: Both formats
   - Optionally specify an export path (directory or file name)

## Output Formats

### HTML Map
- Interactive map using Folium
- Blue lines representing street data
- Automatic browser opening
- Zoom and pan capabilities
- Click on features to view properties
- Layer control for different data types

### SVG File
- Optimized for both traffic and pedestrian data
- Fixed canvas size (1000x1000 pixels)
- Automatic scaling and centering
- Special handling for pedestrian data:
  - Increased spacing between blocks (20% separation)
  - Thicker lines (2px vs 1px for traffic)
  - Only exterior lines drawn for polygons
- Compatible with vector graphics editors
- Suitable for printing and further editing

## Error Handling

- Automatic retries for geocoding (3 attempts)
- Graceful fallback to HTML format if SVG generation fails
- Input validation for all user inputs
- Clear error messages and recovery options
- Automatic coordinate system transformation
- Data validation and cleaning

## Advanced Features

### Coordinate System Handling
- Automatic transformation between coordinate systems
- Support for both geographic and projected coordinates
- Proper handling of buffer calculations

### Data Processing
- Automatic filtering of invalid geometries
- Optimization of large datasets
- Memory-efficient processing
- Support for complex geometry types

### Visualization
- Customizable line styles
- Automatic scaling and centering
- Margin handling
- Support for multiple geometry types

## Example

```python
# Example usage
address = "350 5th Ave, New York, NY 10118"
radius_miles = 0.5
data_type = "traffic"  # or "pedestrian"

# The tool will automatically:
# 1. Geocode the address
# 2. Create a buffer of specified radius
# 3. Extract relevant street data
# 4. Generate visualizations
```

## Troubleshooting

Common issues and solutions:
1. Geocoding failures:
   - Check internet connection
   - Verify address format
   - Try alternative address format
2. SVG generation errors:
   - Check available disk space
   - Verify write permissions
   - Try HTML format as fallback
3. Data loading issues:
   - Verify data file paths
   - Check file permissions
   - Ensure correct file format

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NYC Department of City Planning for providing the data
- OpenStreetMap for geocoding services
- All contributors and users of this tool 