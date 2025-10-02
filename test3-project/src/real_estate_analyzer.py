#!/usr/bin/env python3


import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResults:
    """Data class to store analysis results and statistics."""
    total_properties: int
    valid_properties: int
    invalid_properties: int
    average_price_per_sqft: float
    filtered_properties: int
    filter_percentage: float
    output_file_path: str
    min_price_per_sqft: float
    max_price_per_sqft: float
    median_price_per_sqft: float


class RealEstateAnalyzer:
    """
    Main class for analyzing real estate data and filtering properties
    based on price per square foot criteria.
    """
    
    def __init__(self, input_file: str, output_dir: str = "data/output"):
        """
        Initialize the analyzer with input file and output directory.
        
        Args:
            input_file: Path to the input CSV file
            output_dir: Directory to save output files
        """
        self.input_file = input_file
        self.output_dir = output_dir
        self.df = None
        self.analysis_results = None
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def load_data(self) -> bool:
        """
        Load data from the CSV file and perform initial validation.
        
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading data from: {self.input_file}")
            
            # Check if file exists
            if not os.path.exists(self.input_file):
                logger.error(f"Input file not found: {self.input_file}")
                return False
            
            # Load CSV file
            self.df = pd.read_csv(self.input_file)
            logger.info(f"Successfully loaded {len(self.df)} records")
            
            # Display basic info about the dataset
            logger.info(f"Dataset shape: {self.df.shape}")
            logger.info(f"Columns: {list(self.df.columns)}")
            
            return True
            
        except pd.errors.EmptyDataError:
            logger.error("The CSV file is empty")
            return False
        except pd.errors.ParserError as e:
            logger.error(f"Error parsing CSV file: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading data: {e}")
            return False
    
    def validate_data(self) -> bool:
        """
        Validate that the required columns exist and data is reasonable.
        
        Returns:
            bool: True if data is valid, False otherwise
        """
        try:
            logger.info("Validating data structure and content...")
            
            # Check for required columns (flexible column names)
            price_col = None
            sqft_col = None
            
            # Look for price column
            price_candidates = ['price', 'sale_price', 'selling_price', 'cost']
            for col in self.df.columns:
                if col.lower() in price_candidates:
                    price_col = col
                    break
            
            # Look for square footage column
            sqft_candidates = ['sq__ft', 'square_footage', 'sqft', 'sq_ft', 'area']
            for col in self.df.columns:
                if col.lower() in sqft_candidates or 'sq' in col.lower():
                    sqft_col = col
                    break
            
            if price_col is None:
                logger.error("No price column found. Expected columns: price, sale_price, selling_price, or cost")
                return False
            
            if sqft_col is None:
                logger.error("No square footage column found. Expected columns: sq__ft, square_footage, sqft, sq_ft, or area")
                return False
            
            logger.info(f"Using price column: '{price_col}'")
            logger.info(f"Using square footage column: '{sqft_col}'")
            
            # Store column names for later use
            self.price_col = price_col
            self.sqft_col = sqft_col
            
            # Check for missing values
            price_missing = self.df[price_col].isna().sum()
            sqft_missing = self.df[sqft_col].isna().sum()
            
            logger.info(f"Missing values - Price: {price_missing}, Square footage: {sqft_missing}")
            
            # Check data types and convert if necessary
            self.df[price_col] = pd.to_numeric(self.df[price_col], errors='coerce')
            self.df[sqft_col] = pd.to_numeric(self.df[sqft_col], errors='coerce')
            
            # Check for reasonable value ranges
            valid_prices = (self.df[price_col] > 0) & (self.df[price_col] < 10000000)  # $0 to $10M
            valid_sqft = (self.df[sqft_col] > 0) & (self.df[sqft_col] < 50000)  # 0 to 50,000 sqft
            
            invalid_prices = (~valid_prices).sum()
            invalid_sqft = (~valid_sqft).sum()
            
            if invalid_prices > 0:
                logger.warning(f"Found {invalid_prices} properties with invalid prices")
            if invalid_sqft > 0:
                logger.warning(f"Found {invalid_sqft} properties with invalid square footage")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during data validation: {e}")
            return False
    
    def calculate_price_per_sqft(self) -> None:
        """
        Calculate price per square foot for each property.
        """
        logger.info("Calculating price per square foot...")
        
        # Calculate price per square foot, handling division by zero
        self.df['price_per_sqft'] = np.where(
            (self.df[self.sqft_col] > 0) & (self.df[self.price_col] > 0),
            self.df[self.price_col] / self.df[self.sqft_col],
            np.nan
        )
        
        # Count valid calculations
        valid_calculations = self.df['price_per_sqft'].notna().sum()
        total_properties = len(self.df)
        
        logger.info(f"Successfully calculated price/sqft for {valid_calculations} out of {total_properties} properties")
        
        # Display some statistics
        if valid_calculations > 0:
            min_price_sqft = self.df['price_per_sqft'].min()
            max_price_sqft = self.df['price_per_sqft'].max()
            mean_price_sqft = self.df['price_per_sqft'].mean()
            
            logger.info(f"Price per sqft range: ${min_price_sqft:.2f} - ${max_price_sqft:.2f}")
            logger.info(f"Average price per sqft: ${mean_price_sqft:.2f}")
    
    def filter_below_average(self) -> pd.DataFrame:
        """
        Filter properties with price per square foot below the average.
        
        Returns:
            pd.DataFrame: Filtered dataframe with properties below average price/sqft
        """
        logger.info("Filtering properties below average price per square foot...")
        
        # Calculate average price per square foot (excluding NaN values)
        valid_data = self.df.dropna(subset=['price_per_sqft'])
        
        if len(valid_data) == 0:
            logger.error("No valid price per square foot data available for filtering")
            return pd.DataFrame()
        
        average_price_per_sqft = valid_data['price_per_sqft'].mean()
        logger.info(f"Average price per square foot: ${average_price_per_sqft:.2f}")
        
        # Filter properties below average
        filtered_df = valid_data[valid_data['price_per_sqft'] < average_price_per_sqft].copy()
        
        logger.info(f"Found {len(filtered_df)} properties below average price per square foot")
        logger.info(f"Filter percentage: {(len(filtered_df) / len(valid_data)) * 100:.1f}%")
        
        # Store statistics for results
        self.average_price_per_sqft = average_price_per_sqft
        self.valid_properties = len(valid_data)
        self.filtered_count = len(filtered_df)
        
        return filtered_df
    
    def generate_output_csv(self, filtered_df: pd.DataFrame) -> str:
        """
        Generate output CSV file with filtered properties.
        
        Args:
            filtered_df: DataFrame containing filtered properties
            
        Returns:
            str: Path to the generated output file
        """
        if len(filtered_df) == 0:
            logger.warning("No properties to write to output file")
            return ""
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"filtered_properties_{timestamp}.csv"
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            # Write filtered data to CSV
            filtered_df.to_csv(output_path, index=False)
            logger.info(f"Successfully wrote {len(filtered_df)} properties to: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error writing output file: {e}")
            return ""
    
    def generate_summary_report(self) -> None:
        """
        Generate and display a comprehensive summary report.
        """
        if self.analysis_results is None:
            logger.error("No analysis results available for reporting")
            return
        
        results = self.analysis_results
        
        print("\n" + "="*60)
        print("REAL ESTATE DATA ANALYSIS SUMMARY")
        print("="*60)
        print(f"Input File: {self.input_file}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("DATA PROCESSING SUMMARY:")
        print(f"  Total Properties Loaded: {results.total_properties:,}")
        print(f"  Valid Properties: {results.valid_properties:,}")
        print(f"  Invalid/Missing Data: {results.invalid_properties:,}")
        print()
        
        print("PRICE PER SQUARE FOOT ANALYSIS:")
        print(f"  Average Price/Sqft: ${results.average_price_per_sqft:.2f}")
        print(f"  Minimum Price/Sqft: ${results.min_price_per_sqft:.2f}")
        print(f"  Maximum Price/Sqft: ${results.max_price_per_sqft:.2f}")
        print(f"  Median Price/Sqft: ${results.median_price_per_sqft:.2f}")
        print()
        
        print("FILTERING RESULTS:")
        print(f"  Properties Below Average: {results.filtered_properties:,}")
        print(f"  Filter Percentage: {results.filter_percentage:.1f}%")
        print()
        
        if results.output_file_path:
            print("OUTPUT:")
            print(f"  Generated File: {results.output_file_path}")
            print(f"  File Size: {os.path.getsize(results.output_file_path):,} bytes")
        else:
            print("OUTPUT:")
            print("  No output file generated (no properties met criteria)")
        
        print("="*60)
    
    def run_analysis(self) -> Optional[AnalysisResults]:
        """
        Run the complete analysis workflow.
        
        Returns:
            AnalysisResults: Analysis results and statistics
        """
        try:
            # Step 1: Load data
            if not self.load_data():
                return None
            
            # Step 2: Validate data
            if not self.validate_data():
                return None
            
            # Step 3: Calculate price per square foot
            self.calculate_price_per_sqft()
            
            # Step 4: Filter properties below average
            filtered_df = self.filter_below_average()
            
            # Step 5: Generate output file
            output_path = self.generate_output_csv(filtered_df)
            
            # Step 6: Compile results
            valid_data = self.df.dropna(subset=['price_per_sqft'])
            
            self.analysis_results = AnalysisResults(
                total_properties=len(self.df),
                valid_properties=len(valid_data),
                invalid_properties=len(self.df) - len(valid_data),
                average_price_per_sqft=self.average_price_per_sqft,
                filtered_properties=len(filtered_df),
                filter_percentage=(len(filtered_df) / len(valid_data)) * 100 if len(valid_data) > 0 else 0,
                output_file_path=output_path,
                min_price_per_sqft=valid_data['price_per_sqft'].min() if len(valid_data) > 0 else 0,
                max_price_per_sqft=valid_data['price_per_sqft'].max() if len(valid_data) > 0 else 0,
                median_price_per_sqft=valid_data['price_per_sqft'].median() if len(valid_data) > 0 else 0
            )
            
            # Step 7: Generate summary report
            self.generate_summary_report()
            
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            return None


def main():
    """
    Main function to run the real estate analysis from command line.
    """
    # Default input file (can be overridden by command line argument)
    default_input = "assignment data.csv"
    default_output = "data/output"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = default_input
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = default_output
    
    print("Real Estate Data Analyzer")
    print("=" * 40)
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Create analyzer and run analysis
    analyzer = RealEstateAnalyzer(input_file, output_dir)
    results = analyzer.run_analysis()
    
    if results is None:
        print("Analysis failed. Please check the error messages above.")
        sys.exit(1)
    else:
        print("\nAnalysis completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()