# Test 3 - Real Estate Data Analysis

Python script to analyze real estate sales data and filter properties based on price per square foot.

## Quick Start

1. **Setup:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run analysis:**
   ```bash
   python run_analysis.py
   ```

## What it does

1. Reads `assignment data.csv` (real estate sales data)
2. Calculates price per square foot for each property
3. Finds the average price per square foot
4. Filters properties below the average
5. Generates filtered CSV file in `data/output/`
6. Shows summary statistics

## Usage Options

```bash
# Simple run
python run_analysis.py

# Direct script execution
python src/real_estate_analyzer.py

# Custom input/output
python src/real_estate_analyzer.py "input_file.csv" "output_dir"
```

## Output

- **Filtered CSV file:** `data/output/filtered_properties_YYYYMMDD_HHMMSS.csv`
- **Console summary:** Statistics and analysis results

## Testing

```bash
python -m pytest tests/ -v
```

## Project Structure

```
src/
└── real_estate_analyzer.py    # Main analysis script
data/
├── assignment data.csv        # Input data
└── output/                    # Generated results
tests/
└── test_analyzer.py          # Unit tests
```