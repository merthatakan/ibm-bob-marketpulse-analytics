"""
Store Business Metrics Analysis Script - Enterprise Edition

This module provides comprehensive business intelligence analysis for retail store data,
calculating Customer Lifetime Value (CLV), Customer Acquisition Cost (CAC),
and detecting anomalies in sales patterns.

Author: IBM Bob
Version: 2.0.0
License: MIT
"""

import pandas as pd
import numpy as np
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('store_metrics_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Configuration
@dataclass
class AnalysisConfig:
    """Configuration settings for the analysis."""
    input_file: str = r"C:\Users\Lenovo\OneDrive\Desktop\data\kaggle_store.csv"
    output_file: str = r"C:\Users\Lenovo\OneDrive\Desktop\output.json"
    acquisition_cost_rate: float = 0.20
    outlier_iqr_multiplier: float = 3.0
    unusual_quantity_percentile: float = 0.95
    top_customers_count: int = 10


class DeviationType(Enum):
    """Enumeration for deviation types in anomaly detection."""
    HIGH = "high"
    LOW = "low"


class StoreMetricsAnalyzer:
    """
    Enterprise-grade analyzer for store business metrics.
    
    This class provides comprehensive analysis capabilities including:
    - Customer Lifetime Value (CLV) calculation
    - Customer Acquisition Cost (CAC) estimation
    - Anomaly detection in sales patterns
    - Data cleaning and preparation
    
    Attributes:
        config: Configuration settings for the analysis
        df: Pandas DataFrame containing the store data
        results: Dictionary containing all analysis results
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None) -> None:
        """
        Initialize the analyzer with configuration and load data.
        
        Args:
            config: Optional configuration object. Uses default if not provided.
            
        Raises:
            FileNotFoundError: If the input CSV file doesn't exist
            pd.errors.EmptyDataError: If the CSV file is empty
            ValueError: If required columns are missing
        """
        self.config = config or AnalysisConfig()
        logger.info("Initializing StoreMetricsAnalyzer")
        
        try:
            self._load_and_validate_data()
            self._initialize_results()
            logger.info(f"Successfully loaded {len(self.df)} records")
        except Exception as e:
            logger.error(f"Failed to initialize analyzer: {str(e)}", exc_info=True)
            raise
    
    def _load_and_validate_data(self) -> None:
        """
        Load CSV data and validate required columns.
        
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If required columns are missing
        """
        input_path = Path(self.config.input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        logger.info(f"Loading data from {input_path}")
        self.df = pd.read_csv(input_path)
        
        # Validate required columns
        required_columns = [
            'Order_ID', 'Customer_ID', 'Order_Date', 'Sales', 
            'Profit', 'Quantity', 'Category', 'Region'
        ]
        missing_columns = set(required_columns) - set(self.df.columns)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert date column
        try:
            self.df['Order_Date'] = pd.to_datetime(self.df['Order_Date'])
        except Exception as e:
            logger.error(f"Failed to parse Order_Date column: {str(e)}")
            raise ValueError(f"Invalid date format in Order_Date column: {str(e)}")
        
        logger.info("Data validation successful")
    
    def _initialize_results(self) -> None:
        """Initialize the results dictionary with metadata."""
        try:
            self.results: Dict[str, Any] = {
                'metadata': {
                    'analysis_date': datetime.now().isoformat(),
                    'total_records': int(len(self.df)),
                    'date_range': {
                        'start': self.df['Order_Date'].min().strftime('%Y-%m-%d'),
                        'end': self.df['Order_Date'].max().strftime('%Y-%m-%d')
                    },
                    'version': '2.0.0',
                    'analyzer': 'IBM Bob Enterprise Store Metrics Analyzer'
                },
                'business_metrics': {},
                'anomalies': {},
                'cleaned_data': []
            }
        except Exception as e:
            logger.error(f"Failed to initialize results: {str(e)}")
            raise
    
    def calculate_clv(self) -> pd.DataFrame:
        """
        Calculate Customer Lifetime Value (CLV) for all customers.
        
        CLV Formula: Average Purchase Value × Purchase Frequency × Customer Lifespan
        
        Returns:
            DataFrame containing customer statistics and CLV calculations
            
        Raises:
            ValueError: If calculation fails due to data issues
        """
        logger.info("Calculating Customer Lifetime Value (CLV)")
        
        try:
            # Group by customer and calculate aggregates
            customer_stats = self.df.groupby('Customer_ID').agg({
                'Sales': ['sum', 'mean', 'count'],
                'Profit': 'sum',
                'Order_Date': ['min', 'max']
            }).reset_index()
            
            # Flatten column names
            customer_stats.columns = [
                'Customer_ID', 'Total_Sales', 'Avg_Purchase_Value', 
                'Purchase_Count', 'Total_Profit', 'First_Order', 'Last_Order'
            ]
            
            # Calculate customer lifespan in days
            customer_stats['Lifespan_Days'] = (
                customer_stats['Last_Order'] - customer_stats['First_Order']
            ).dt.days + 1
            
            # Calculate purchase frequency (purchases per day)
            customer_stats['Purchase_Frequency'] = (
                customer_stats['Purchase_Count'] / customer_stats['Lifespan_Days']
            )
            
            # Calculate CLV
            customer_stats['CLV'] = (
                customer_stats['Avg_Purchase_Value'] * 
                customer_stats['Purchase_Frequency'] * 
                customer_stats['Lifespan_Days']
            )
            
            # Calculate overall metrics
            total_customers = len(customer_stats)
            avg_clv = customer_stats['CLV'].mean()
            median_clv = customer_stats['CLV'].median()
            total_clv = customer_stats['CLV'].sum()
            std_clv = customer_stats['CLV'].std()
            
            # Get top customers
            top_customers = customer_stats.nlargest(
                self.config.top_customers_count, 'CLV'
            )[['Customer_ID', 'CLV', 'Total_Sales', 'Purchase_Count', 'Avg_Purchase_Value']]
            
            # Store results
            self.results['business_metrics']['customer_lifetime_value'] = {
                'total_customers': int(total_customers),
                'average_clv': round(float(avg_clv), 2),
                'median_clv': round(float(median_clv), 2),
                'std_clv': round(float(std_clv), 2),
                'total_clv': round(float(total_clv), 2),
                'top_customers': [
                    {
                        'customer_id': str(c['Customer_ID']),
                        'clv': round(float(c['CLV']), 2),
                        'total_sales': round(float(c['Total_Sales']), 2),
                        'purchase_count': int(c['Purchase_Count']),
                        'avg_purchase_value': round(float(c['Avg_Purchase_Value']), 2)
                    }
                    for _, c in top_customers.iterrows()
                ]
            }
            
            logger.info(f"CLV calculated for {total_customers} customers")
            logger.info(f"Average CLV: ${avg_clv:.2f}, Median CLV: ${median_clv:.2f}")
            
            return customer_stats
            
        except Exception as e:
            logger.error(f"Failed to calculate CLV: {str(e)}", exc_info=True)
            raise ValueError(f"CLV calculation failed: {str(e)}")
    
    def calculate_cac(self) -> None:
        """
        Calculate Customer Acquisition Cost (CAC) estimation.
        
        Since marketing spend data is not available, CAC is estimated as:
        CAC = (Total Costs × Acquisition Rate) / Total Customers
        
        Raises:
            ValueError: If calculation fails due to data issues
        """
        logger.info("Calculating Customer Acquisition Cost (CAC)")
        
        try:
            total_sales = self.df['Sales'].sum()
            total_profit = self.df['Profit'].sum()
            total_costs = total_sales - total_profit
            total_customers = self.df['Customer_ID'].nunique()
            
            # Estimate acquisition costs
            estimated_total_acquisition_cost = (
                total_costs * self.config.acquisition_cost_rate
            )
            estimated_cac = estimated_total_acquisition_cost / total_customers
            
            # Calculate by region
            region_stats = self.df.groupby('Region').agg({
                'Sales': 'sum',
                'Profit': 'sum',
                'Customer_ID': 'nunique'
            }).reset_index()
            
            region_stats['Costs'] = region_stats['Sales'] - region_stats['Profit']
            region_stats['Estimated_CAC'] = (
                region_stats['Costs'] * self.config.acquisition_cost_rate / 
                region_stats['Customer_ID']
            )
            
            region_cac = [
                {
                    'region': str(row['Region']),
                    'estimated_cac': round(float(row['Estimated_CAC']), 2),
                    'customers': int(row['Customer_ID']),
                    'total_sales': round(float(row['Sales']), 2),
                    'total_profit': round(float(row['Profit']), 2)
                }
                for _, row in region_stats.iterrows()
            ]
            
            # Store results
            self.results['business_metrics']['customer_acquisition_cost'] = {
                'methodology': f'CAC estimated as {self.config.acquisition_cost_rate*100}% of total costs divided by customer count',
                'total_customers': int(total_customers),
                'total_sales': round(float(total_sales), 2),
                'total_profit': round(float(total_profit), 2),
                'total_costs': round(float(total_costs), 2),
                'estimated_total_acquisition_cost': round(float(estimated_total_acquisition_cost), 2),
                'estimated_average_cac': round(float(estimated_cac), 2),
                'cac_by_region': region_cac
            }
            
            logger.info(f"Estimated Average CAC: ${estimated_cac:.2f}")
            logger.info(f"CAC calculated for {len(region_cac)} regions")
            
        except Exception as e:
            logger.error(f"Failed to calculate CAC: {str(e)}", exc_info=True)
            raise ValueError(f"CAC calculation failed: {str(e)}")
    
    def detect_anomalies(self) -> None:
        """
        Detect anomalies in the dataset using multiple methods.
        
        Anomaly types detected:
        1. Negative profit margins
        2. Extreme sales outliers (IQR method)
        3. Unusual quantity orders
        
        Raises:
            ValueError: If anomaly detection fails
        """
        logger.info("Detecting anomalies in dataset")
        
        try:
            anomalies: Dict[str, Any] = {
                'negative_profit_margins': [],
                'extreme_sales_outliers': [],
                'unusual_quantities': [],
                'summary': {}
            }
            
            # 1. Negative Profit Margins
            negative_profit = self.df[self.df['Profit'] < 0].copy()
            negative_profit['Profit_Margin'] = (
                negative_profit['Profit'] / negative_profit['Sales']
            ) * 100
            
            anomalies['negative_profit_margins'] = [
                {
                    'order_id': str(row['Order_ID']),
                    'customer_id': str(row['Customer_ID']),
                    'sales': round(float(row['Sales']), 2),
                    'profit': round(float(row['Profit']), 2),
                    'profit_margin_pct': round(float(row['Profit_Margin']), 2),
                    'category': str(row['Category']),
                    'region': str(row['Region']),
                    'order_date': row['Order_Date'].strftime('%Y-%m-%d')
                }
                for _, row in negative_profit.iterrows()
            ]
            
            logger.info(f"Found {len(negative_profit)} orders with negative profit margins")
            
            # 2. Extreme Sales Outliers (IQR method)
            Q1 = self.df['Sales'].quantile(0.25)
            Q3 = self.df['Sales'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - self.config.outlier_iqr_multiplier * IQR
            upper_bound = Q3 + self.config.outlier_iqr_multiplier * IQR
            
            sales_outliers = self.df[
                (self.df['Sales'] < lower_bound) | (self.df['Sales'] > upper_bound)
            ].copy()
            
            anomalies['extreme_sales_outliers'] = [
                {
                    'order_id': str(row['Order_ID']),
                    'customer_id': str(row['Customer_ID']),
                    'sales': round(float(row['Sales']), 2),
                    'profit': round(float(row['Profit']), 2),
                    'quantity': int(row['Quantity']),
                    'category': str(row['Category']),
                    'region': str(row['Region']),
                    'order_date': row['Order_Date'].strftime('%Y-%m-%d'),
                    'deviation': DeviationType.HIGH.value if row['Sales'] > upper_bound 
                                else DeviationType.LOW.value
                }
                for _, row in sales_outliers.iterrows()
            ]
            
            logger.info(f"Found {len(sales_outliers)} extreme sales outliers")
            logger.info(f"Sales IQR range: ${lower_bound:.2f} - ${upper_bound:.2f}")
            
            # 3. Unusual Quantities
            quantity_threshold = self.df['Quantity'].quantile(
                self.config.unusual_quantity_percentile
            )
            unusual_qty = self.df[self.df['Quantity'] > quantity_threshold].copy()
            
            anomalies['unusual_quantities'] = [
                {
                    'order_id': str(row['Order_ID']),
                    'customer_id': str(row['Customer_ID']),
                    'quantity': int(row['Quantity']),
                    'sales': round(float(row['Sales']), 2),
                    'profit': round(float(row['Profit']), 2),
                    'category': str(row['Category']),
                    'region': str(row['Region']),
                    'order_date': row['Order_Date'].strftime('%Y-%m-%d')
                }
                for _, row in unusual_qty.iterrows()
            ]
            
            logger.info(f"Found {len(unusual_qty)} orders with unusual quantities (>{quantity_threshold:.0f})")
            
            # Summary statistics
            anomalies['summary'] = {
                'total_anomalies': len(negative_profit) + len(sales_outliers) + len(unusual_qty),
                'negative_profit_count': len(negative_profit),
                'negative_profit_total_loss': round(float(negative_profit['Profit'].sum()), 2),
                'sales_outliers_count': len(sales_outliers),
                'unusual_quantity_count': len(unusual_qty),
                'sales_outlier_bounds': {
                    'lower': round(float(lower_bound), 2),
                    'upper': round(float(upper_bound), 2),
                    'Q1': round(float(Q1), 2),
                    'Q3': round(float(Q3), 2),
                    'IQR': round(float(IQR), 2)
                },
                'quantity_threshold': round(float(quantity_threshold), 2)
            }
            
            self.results['anomalies'] = anomalies
            logger.info(f"Anomaly detection complete. Total anomalies: {anomalies['summary']['total_anomalies']}")
            
        except Exception as e:
            logger.error(f"Failed to detect anomalies: {str(e)}", exc_info=True)
            raise ValueError(f"Anomaly detection failed: {str(e)}")
    
    def clean_and_prepare_data(self) -> None:
        """
        Prepare cleaned and enriched dataset for output.
        
        Adds calculated fields:
        - Profit margin percentage
        - Revenue per unit
        - Profitability flag
        
        Raises:
            ValueError: If data preparation fails
        """
        logger.info("Preparing cleaned and enriched data")
        
        try:
            cleaned = self.df.copy()
            cleaned['Profit_Margin'] = (cleaned['Profit'] / cleaned['Sales']) * 100
            cleaned['Revenue_Per_Unit'] = cleaned['Sales'] / cleaned['Quantity']
            cleaned['Is_Profitable'] = cleaned['Profit'] > 0
            
            self.results['cleaned_data'] = [
                {
                    'order_id': str(row['Order_ID']),
                    'customer_id': str(row['Customer_ID']),
                    'sales': round(float(row['Sales']), 2),
                    'profit': round(float(row['Profit']), 2),
                    'profit_margin_pct': round(float(row['Profit_Margin']), 2),
                    'quantity': int(row['Quantity']),
                    'revenue_per_unit': round(float(row['Revenue_Per_Unit']), 2),
                    'category': str(row['Category']),
                    'region': str(row['Region']),
                    'order_date': row['Order_Date'].strftime('%Y-%m-%d'),
                    'is_profitable': bool(row['Is_Profitable'])
                }
                for _, row in cleaned.iterrows()
            ]
            
            logger.info(f"Prepared {len(self.results['cleaned_data'])} cleaned records")
            
        except Exception as e:
            logger.error(f"Failed to prepare cleaned data: {str(e)}", exc_info=True)
            raise ValueError(f"Data preparation failed: {str(e)}")
    
    def save_results(self, output_path: Optional[str] = None) -> None:
        """
        Save analysis results to JSON file.
        
        Args:
            output_path: Optional custom output path. Uses config default if not provided.
            
        Raises:
            IOError: If file writing fails
        """
        output_path = output_path or self.config.output_file
        output_file = Path(output_path)
        
        logger.info(f"Saving results to {output_file}")
        
        try:
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            logger.info("Results saved successfully")
            logger.info(f"Output contains: {len(self.results['cleaned_data'])} records, "
                       f"{self.results['anomalies']['summary']['total_anomalies']} anomalies")
            
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}", exc_info=True)
            raise IOError(f"Failed to save results to {output_file}: {str(e)}")
    
    def run_analysis(self) -> Dict[str, Any]:
        """
        Execute the complete analysis pipeline.
        
        Returns:
            Dictionary containing all analysis results
            
        Raises:
            Exception: If any step of the analysis fails
        """
        logger.info("="*60)
        logger.info("STARTING STORE BUSINESS METRICS ANALYSIS")
        logger.info("="*60)
        
        try:
            # Execute analysis steps
            self.calculate_clv()
            self.calculate_cac()
            self.detect_anomalies()
            self.clean_and_prepare_data()
            self.save_results()
            
            logger.info("="*60)
            logger.info("ANALYSIS COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            
            return self.results
            
        except Exception as e:
            logger.error(f"Analysis pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a concise summary of analysis results.
        
        Returns:
            Dictionary containing key metrics and findings
        """
        try:
            return {
                'total_records': self.results['metadata']['total_records'],
                'total_customers': self.results['business_metrics']['customer_lifetime_value']['total_customers'],
                'average_clv': self.results['business_metrics']['customer_lifetime_value']['average_clv'],
                'estimated_cac': self.results['business_metrics']['customer_acquisition_cost']['estimated_average_cac'],
                'clv_to_cac_ratio': round(
                    self.results['business_metrics']['customer_lifetime_value']['average_clv'] /
                    self.results['business_metrics']['customer_acquisition_cost']['estimated_average_cac'],
                    2
                ),
                'total_anomalies': self.results['anomalies']['summary']['total_anomalies'],
                'negative_profit_orders': self.results['anomalies']['summary']['negative_profit_count'],
                'sales_outliers': self.results['anomalies']['summary']['sales_outliers_count'],
                'unusual_quantities': self.results['anomalies']['summary']['unusual_quantity_count']
            }
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return {}


def main() -> int:
    """
    Main execution function with comprehensive error handling.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Initializing Store Metrics Analyzer")
        
        # Initialize analyzer with default configuration
        config = AnalysisConfig()
        analyzer = StoreMetricsAnalyzer(config)
        
        # Run analysis
        results = analyzer.run_analysis()
        
        # Print summary
        summary = analyzer.get_summary()
        print("\n" + "="*60)
        print("ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Records Analyzed: {summary.get('total_records', 'N/A')}")
        print(f"Total Customers: {summary.get('total_customers', 'N/A')}")
        print(f"Average CLV: ${summary.get('average_clv', 0):.2f}")
        print(f"Estimated Average CAC: ${summary.get('estimated_cac', 0):.2f}")
        print(f"CLV/CAC Ratio: {summary.get('clv_to_cac_ratio', 0):.2f}x")
        print(f"\nAnomalies Detected: {summary.get('total_anomalies', 0)}")
        print(f"  - Negative Profit Orders: {summary.get('negative_profit_orders', 0)}")
        print(f"  - Sales Outliers: {summary.get('sales_outliers', 0)}")
        print(f"  - Unusual Quantities: {summary.get('unusual_quantities', 0)}")
        print("="*60)
        
        logger.info("Application completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        print(f"\n[ERROR] Input file not found. Please check the file path in configuration.")
        return 1
        
    except ValueError as e:
        logger.error(f"Data validation error: {str(e)}")
        print(f"\n[ERROR] Data validation failed: {str(e)}")
        return 1
        
    except IOError as e:
        logger.error(f"I/O error: {str(e)}")
        print(f"\n[ERROR] File operation failed: {str(e)}")
        return 1
        
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"\n[ERROR] An unexpected error occurred: {str(e)}")
        print("Check store_metrics_analysis.log for detailed error information.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


# Made with ❤️ by IBM Bob - Enterprise Analytics Solution

# Made with Bob
