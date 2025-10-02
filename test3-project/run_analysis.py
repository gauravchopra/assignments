#!/usr/bin/env python3
"""
Simple script to run the real estate analysis on the assignment data.

This script provides an easy way to run the analysis without command line arguments.
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from real_estate_analyzer import RealEstateAnalyzer


def main():
    """Run the analysis on the assignment data file."""
    
    # Configuration
    input_file = "assignment data.csv"
    output_dir = "data/output"
    
    print("Real Estate Data Analysis - Assignment")
    print("=" * 50)
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"ERROR: Input file '{input_file}' not found!")
        print("Please ensure the assignment data.csv file is in the project root directory.")
        return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the analysis
    try:
        analyzer = RealEstateAnalyzer(input_file, output_dir)
        results = analyzer.run_analysis()
        
        if results is None:
            print("Analysis failed. Please check the error messages above.")
            return 1
        else:
            print("\n✅ Analysis completed successfully!")
            print(f"📊 Processed {results.total_properties:,} properties")
            print(f"📈 Average price per sqft: ${results.average_price_per_sqft:.2f}")
            print(f"🏠 Properties below average: {results.filtered_properties:,} ({results.filter_percentage:.1f}%)")
            
            if results.output_file_path:
                print(f"📄 Output file: {results.output_file_path}")
            
            return 0
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)