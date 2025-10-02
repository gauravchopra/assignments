#!/usr/bin/env python3
"""
Unit tests for the Real Estate Analyzer

This module contains basic tests for the real estate analysis functionality.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from real_estate_analyzer import RealEstateAnalyzer, AnalysisResults


class TestRealEstateAnalyzer(unittest.TestCase):
    """Test cases for RealEstateAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create sample test data
        self.sample_data = {
            'street': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St'],
            'price': [250000, 180000, 350000, 200000],
            'sq__ft': [1200, 900, 1800, 1000],
            'beds': [3, 2, 4, 3],
            'baths': [2, 1, 3, 2]
        }
        
        # Create temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df = pd.DataFrame(self.sample_data)
        df.to_csv(self.temp_file.name, index=False)
        self.temp_file.close()
        
        # Create temporary output directory
        self.temp_output_dir = tempfile.mkdtemp()
        
        # Initialize analyzer
        self.analyzer = RealEstateAnalyzer(self.temp_file.name, self.temp_output_dir)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Remove temporary files
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        
        # Clean up output directory
        for file in os.listdir(self.temp_output_dir):
            os.unlink(os.path.join(self.temp_output_dir, file))
        os.rmdir(self.temp_output_dir)
    
    def test_load_data(self):
        """Test data loading functionality."""
        result = self.analyzer.load_data()
        self.assertTrue(result)
        self.assertIsNotNone(self.analyzer.df)
        self.assertEqual(len(self.analyzer.df), 4)
    
    def test_validate_data(self):
        """Test data validation functionality."""
        self.analyzer.load_data()
        result = self.analyzer.validate_data()
        self.assertTrue(result)
        self.assertEqual(self.analyzer.price_col, 'price')
        self.assertEqual(self.analyzer.sqft_col, 'sq__ft')
    
    def test_calculate_price_per_sqft(self):
        """Test price per square foot calculation."""
        self.analyzer.load_data()
        self.analyzer.validate_data()
        self.analyzer.calculate_price_per_sqft()
        
        # Check that price_per_sqft column was created
        self.assertIn('price_per_sqft', self.analyzer.df.columns)
        
        # Check specific calculations
        expected_values = [
            250000 / 1200,  # 208.33
            180000 / 900,   # 200.00
            350000 / 1800,  # 194.44
            200000 / 1000   # 200.00
        ]
        
        for i, expected in enumerate(expected_values):
            self.assertAlmostEqual(self.analyzer.df.iloc[i]['price_per_sqft'], expected, places=2)
    
    def test_filter_below_average(self):
        """Test filtering functionality."""
        self.analyzer.load_data()
        self.analyzer.validate_data()
        self.analyzer.calculate_price_per_sqft()
        
        filtered_df = self.analyzer.filter_below_average()
        
        # Calculate expected average: (208.33 + 200.00 + 194.44 + 200.00) / 4 = 200.69
        # Properties below average should be: 194.44 and 200.00 (2 properties)
        self.assertGreater(len(filtered_df), 0)
        self.assertLess(len(filtered_df), len(self.analyzer.df))
    
    def test_run_analysis(self):
        """Test complete analysis workflow."""
        results = self.analyzer.run_analysis()
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, AnalysisResults)
        self.assertEqual(results.total_properties, 4)
        self.assertEqual(results.valid_properties, 4)
        self.assertEqual(results.invalid_properties, 0)
        self.assertGreater(results.average_price_per_sqft, 0)
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent input file."""
        analyzer = RealEstateAnalyzer("nonexistent_file.csv", self.temp_output_dir)
        result = analyzer.load_data()
        self.assertFalse(result)
    
    def test_empty_dataframe(self):
        """Test handling of empty data."""
        # Create empty CSV file
        empty_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        empty_file.write("price,sq__ft\n")  # Header only
        empty_file.close()
        
        try:
            analyzer = RealEstateAnalyzer(empty_file.name, self.temp_output_dir)
            analyzer.load_data()
            filtered_df = analyzer.filter_below_average() if hasattr(analyzer, 'df') else pd.DataFrame()
            self.assertEqual(len(filtered_df), 0)
        finally:
            os.unlink(empty_file.name)


class TestDataValidation(unittest.TestCase):
    """Test cases for data validation functionality."""
    
    def test_missing_required_columns(self):
        """Test handling of missing required columns."""
        # Create CSV without required columns
        invalid_data = pd.DataFrame({
            'address': ['123 Main St'],
            'bedrooms': [3]
        })
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        invalid_data.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        try:
            temp_output_dir = tempfile.mkdtemp()
            analyzer = RealEstateAnalyzer(temp_file.name, temp_output_dir)
            analyzer.load_data()
            result = analyzer.validate_data()
            self.assertFalse(result)
        finally:
            os.unlink(temp_file.name)
            os.rmdir(temp_output_dir)
    
    def test_invalid_data_types(self):
        """Test handling of invalid data types."""
        # Create CSV with invalid data types
        invalid_data = pd.DataFrame({
            'price': ['not_a_number', 100000],
            'sq__ft': [1000, 'invalid']
        })
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        invalid_data.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        try:
            temp_output_dir = tempfile.mkdtemp()
            analyzer = RealEstateAnalyzer(temp_file.name, temp_output_dir)
            analyzer.load_data()
            result = analyzer.validate_data()
            # Should still return True but handle the invalid data
            self.assertTrue(result)
        finally:
            os.unlink(temp_file.name)
            os.rmdir(temp_output_dir)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)