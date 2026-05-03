import csv
import random
from datetime import datetime, timedelta
import os

# Configuration
OUTPUT_FILE = r"C:\Users\Lenovo\OneDrive\Desktop\data\kaggle_store.csv"
NUM_ROWS = 500

# Data generation parameters
CATEGORIES = ["Furniture", "Office Supplies", "Technology"]
REGIONS = ["East", "West", "Central", "South"]
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

def generate_order_id(index):
    """Generate unique order ID"""
    return f"ORD-2024-{index:05d}"

def generate_customer_id():
    """Generate customer ID"""
    return f"CUST-{random.randint(1, 200):05d}"

def generate_sales():
    """Generate realistic sales amount"""
    # Use different ranges for different price points
    price_tier = random.choices(
        [1, 2, 3, 4],
        weights=[40, 30, 20, 10],  # More low-price items
        k=1
    )[0]
    
    if price_tier == 1:
        return round(random.uniform(10, 100), 2)
    elif price_tier == 2:
        return round(random.uniform(100, 500), 2)
    elif price_tier == 3:
        return round(random.uniform(500, 1500), 2)
    else:
        return round(random.uniform(1500, 5000), 2)

def generate_profit(sales):
    """Generate profit based on sales (10-30% margin, with some losses)"""
    # 85% profitable, 15% loss
    if random.random() < 0.85:
        margin = random.uniform(0.10, 0.30)
        return round(sales * margin, 2)
    else:
        # Loss scenario (discounts, returns, etc.)
        loss = random.uniform(0.05, 0.20)
        return round(-sales * loss, 2)

def generate_quantity():
    """Generate quantity ordered"""
    # Most orders are small quantities
    weights = [50, 25, 15, 7, 3]  # Decreasing probability
    quantities = [1, 2, 3, 4, 5]
    
    qty = random.choices(quantities, weights=weights, k=1)[0]
    
    # Occasionally larger orders
    if random.random() < 0.1:
        qty = random.randint(6, 20)
    
    return qty

def generate_order_date():
    """Generate random order date between START_DATE and END_DATE"""
    time_between = END_DATE - START_DATE
    days_between = time_between.days
    random_days = random.randint(0, days_between)
    order_date = START_DATE + timedelta(days=random_days)
    return order_date.strftime("%Y-%m-%d")

def generate_dataset():
    """Generate the complete dataset"""
    print(f"Generating {NUM_ROWS} rows of synthetic Global Super Store data...")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Open CSV file for writing
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Order_ID', 'Customer_ID', 'Sales', 'Profit', 'Quantity', 'Category', 'Region', 'Order_Date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Generate rows
        for i in range(1, NUM_ROWS + 1):
            sales = generate_sales()
            profit = generate_profit(sales)
            
            row = {
                'Order_ID': generate_order_id(i),
                'Customer_ID': generate_customer_id(),
                'Sales': sales,
                'Profit': profit,
                'Quantity': generate_quantity(),
                'Category': random.choice(CATEGORIES),
                'Region': random.choice(REGIONS),
                'Order_Date': generate_order_date()
            }
            
            writer.writerow(row)
            
            # Progress indicator
            if i % 100 == 0:
                print(f"  Generated {i}/{NUM_ROWS} rows...")
    
    print(f"\n[SUCCESS] Dataset successfully created at: {OUTPUT_FILE}")
    print(f"[SUCCESS] Total rows: {NUM_ROWS}")
    print(f"[SUCCESS] Columns: {', '.join(fieldnames)}")
    
    # Display sample statistics
    print("\n--- Sample Statistics ---")
    print(f"Categories: {', '.join(CATEGORIES)}")
    print(f"Regions: {', '.join(REGIONS)}")
    print(f"Date Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
    print(f"Customer Pool: ~200 unique customers")

if __name__ == "__main__":
    generate_dataset()

# Made with Bob
