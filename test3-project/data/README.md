# Data Directory

This directory contains input and output data files for the real estate analysis.

## Structure

- `sales-data.csv` - Input file containing real estate sales data (to be provided)
- `output/` - Directory for generated filtered CSV files
- `samples/` - Sample data files for testing

## Input File Format

The `sales-data.csv` file should contain the following columns:

### Required Columns
- `price` - Sale price of the property (numeric)
- `square_footage` - Square footage of the property (numeric)

### Optional Columns
- `address` - Property address (string)
- `bedrooms` - Number of bedrooms (integer)
- `bathrooms` - Number of bathrooms (numeric)
- `year_built` - Year the property was built (integer)
- `property_type` - Type of property (string)

### Example Format
```csv
address,price,square_footage,bedrooms,bathrooms,year_built,property_type
"123 Main St",250000,1200,3,2,1995,Single Family
"456 Oak Ave",180000,900,2,1,1980,Condo
"789 Pine Rd",350000,1800,4,3,2005,Single Family
```

## Output Files

Generated files will be placed in the `output/` directory with timestamps:
- `filtered_properties_YYYYMMDD_HHMMSS.csv` - Properties below average price/sqft