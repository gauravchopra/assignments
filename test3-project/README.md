# Test 3 - Real Estate Data Analysis

This is the third test assignment focused on analyzing real estate sales data using Python to filter properties based on price per square foot criteria.

## Assignment Overview

**Objective**: Process a CSV file containing real estate sale prices and generate a new CSV file that only includes properties sold for less than the average price per square foot.

**Input**: `sales-data.csv` - Real estate sales data
**Output**: Filtered CSV file with properties below average price/sqft
**Technology**: Python with CSV processing

## Project Structure

```
test3-project/
├── src/
│   └── real_estate_analyzer.py    # Main analysis script
├── data/
│   ├── sales-data.csv            # Input data file (to be provided)
│   └── output/                   # Generated output files
├── tests/
│   └── test_analyzer.py          # Unit tests
├── .kiro/specs/                  # Kiro specifications
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
└── README.md                     # This file
```

## Requirements

- Python 3.8+
- pandas (for CSV processing)
- numpy (for statistical calculations)

## Quick Start

1. **Setup Environment**:
   ```bash
   cd test3-project
   python3 -m venv venv
   source venv/bin/activate  # On Linux/Mac
   pip install -r requirements.txt
   ```

2. **Data File**:
   - The input file `assignment data.csv` is already provided in the project root

3. **Run Analysis** (Choose one method):
   
   **Method 1 - Simple Run Script**:
   ```bash
   python run_analysis.py
   ```
   
   **Method 2 - Direct Script Execution**:
   ```bash
   python src/real_estate_analyzer.py
   ```
   
   **Method 3 - Custom Input/Output**:
   ```bash
   python src/real_estate_analyzer.py "assignment data.csv" "custom_output_dir"
   ```

4. **View Results**:
   - Check `data/output/` for the filtered CSV file
   - View the comprehensive summary report in the console

## Expected Functionality

The script will:
1. Read the input CSV file (`sales-data.csv`)
2. Calculate price per square foot for each property
3. Determine the average price per square foot across all properties
4. Filter properties with price/sqft below the average
5. Generate a new CSV file with the filtered results
6. Provide summary statistics

## Data Processing Steps

1. **Data Loading**: Read CSV file into memory
2. **Data Validation**: Check for required columns and data quality
3. **Price Calculation**: Compute price per square foot (price ÷ square footage)
4. **Statistical Analysis**: Calculate average price per square foot
5. **Filtering**: Select properties below average price/sqft
6. **Output Generation**: Write filtered data to new CSV file
7. **Reporting**: Display summary statistics

## Expected Output

### Console Output
The script provides a comprehensive summary report including:
- Total properties processed
- Data validation results
- Average price per square foot calculation
- Number of properties below average
- Filter percentage
- Output file location

### Generated Files
- **Filtered CSV File**: `data/output/filtered_properties_YYYYMMDD_HHMMSS.csv`
  - Contains only properties with price/sqft below the calculated average
  - Includes all original columns plus calculated `price_per_sqft` column
  - Maintains original data format and structure

### Sample Output
```
REAL ESTATE DATA ANALYSIS SUMMARY
============================================================
Input File: assignment data.csv
Analysis Date: 2024-01-15 14:30:25

DATA PROCESSING SUMMARY:
  Total Properties Loaded: 985
  Valid Properties: 985
  Invalid/Missing Data: 0

PRICE PER SQUARE FOOT ANALYSIS:
  Average Price/Sqft: $123.45
  Minimum Price/Sqft: $45.67
  Maximum Price/Sqft: $234.56
  Median Price/Sqft: $118.90

FILTERING RESULTS:
  Properties Below Average: 492
  Filter Percentage: 49.9%

OUTPUT:
  Generated File: data/output/filtered_properties_20240115_143025.csv
  File Size: 45,678 bytes
============================================================
```

## Testing

Run the unit tests to verify functionality:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python tests/test_analyzer.py

# Run tests with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Data Analysis Details

The script performs the following analysis steps:

1. **Data Loading**: Reads the CSV file and validates structure
2. **Column Detection**: Automatically detects price and square footage columns
3. **Data Validation**: Checks for reasonable value ranges and data types
4. **Price Calculation**: Computes price per square foot (price ÷ square footage)
5. **Statistical Analysis**: Calculates average, min, max, and median price/sqft
6. **Filtering**: Selects properties with price/sqft below the average
7. **Output Generation**: Creates filtered CSV with timestamp
8. **Reporting**: Displays comprehensive analysis summary

## Troubleshooting

### Common Issues

1. **File Not Found**: Ensure `assignment data.csv` is in the project root
2. **Permission Errors**: Check write permissions for `data/output/` directory
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Invalid Data**: Check CSV format and required columns (price, square footage)

### Data Requirements

- **Required Columns**: The script automatically detects columns for:
  - Price: `price`, `sale_price`, `selling_price`, or `cost`
  - Square Footage: `sq__ft`, `square_footage`, `sqft`, `sq_ft`, or `area`
- **Data Format**: Numeric values for price and square footage
- **File Format**: Standard CSV with header row

---

**Note**: This is Test 3 - A Python data analysis assignment for processing real estate sales data. Not intended for production deployment.