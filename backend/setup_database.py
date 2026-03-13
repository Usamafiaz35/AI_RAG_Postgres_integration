"""
Sample Data Insertion Script
============================

This script directly inserts sample data into the financial tables.
Use this if you prefer to insert data directly without reading from schema.sql.

Usage:
    python insert_sample_data.py
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

def get_database_connection():
    """Create and return a database connection."""
    
    USER = os.getenv("SUPABASE_USER")
    PASSWORD = os.getenv("SUPABASE_PASSWORD")
    HOST = os.getenv("SUPABASE_HOST")
    PORT = os.getenv("SUPABASE_PORT", "5432")
    DATABASE = os.getenv("SUPABASE_DATABASE", "postgres")
    
    if not all([USER, PASSWORD, HOST]):
        raise RuntimeError("Missing required database credentials in .env file")
    
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=require"
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    return engine

def create_tables(engine):
    """Create the financial tables if they don't exist."""
    
    create_tables_sql = """
    -- Create tables if they don't exist
    CREATE TABLE IF NOT EXISTS financial_agent_balancesheets (
      id SERIAL PRIMARY KEY,
      month VARCHAR NOT NULL,
      total_assets REAL NOT NULL,
      total_liabilities REAL NOT NULL,
      equity REAL NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS financial_agent_pl_reports (
      id SERIAL PRIMARY KEY,
      month VARCHAR NOT NULL,
      revenue REAL NOT NULL,
      cost_of_goods_sold REAL NOT NULL,
      operating_expenses REAL NOT NULL,
      net_profit REAL NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_tables_sql))
        conn.commit()
        print("Tables created successfully")

def insert_sample_data(engine):
    """Insert sample data into both tables."""
    
    # Sample P&L data
    pl_data = [
        ('2024-01', 150000.00, 75000.00, 45000.00, 30000.00),
        ('2024-02', 165000.00, 82500.00, 48000.00, 34500.00),
        ('2024-03', 180000.00, 90000.00, 52000.00, 38000.00),
        ('2024-04', 155000.00, 77500.00, 46000.00, 31500.00),
        ('2024-05', 175000.00, 87500.00, 50000.00, 37500.00),
        ('2024-06', 190000.00, 95000.00, 55000.00, 40000.00),
        ('2024-07', 200000.00, 100000.00, 58000.00, 42000.00),
        ('2024-08', 185000.00, 92500.00, 53000.00, 39500.00),
        ('2024-09', 210000.00, 105000.00, 60000.00, 45000.00),
        ('2024-10', 195000.00, 97500.00, 56000.00, 41500.00),
        ('2024-11', 220000.00, 110000.00, 63000.00, 47000.00),
        ('2024-12', 230000.00, 115000.00, 65000.00, 50000.00),
        ('2025-01', 240000.00, 120000.00, 68000.00, 52000.00),
        ('2025-02', 225000.00, 112500.00, 64000.00, 48500.00),
        ('2025-03', 250000.00, 125000.00, 72000.00, 53000.00)
    ]
    
    # Sample Balance Sheet data
    bs_data = [
        ('2024-01', 500000.00, 200000.00, 300000.00),
        ('2024-02', 520000.00, 210000.00, 310000.00),
        ('2024-03', 540000.00, 215000.00, 325000.00),
        ('2024-04', 530000.00, 220000.00, 310000.00),
        ('2024-05', 550000.00, 225000.00, 325000.00),
        ('2024-06', 570000.00, 230000.00, 340000.00),
        ('2024-07', 590000.00, 235000.00, 355000.00),
        ('2024-08', 580000.00, 240000.00, 340000.00),
        ('2024-09', 610000.00, 245000.00, 365000.00),
        ('2024-10', 600000.00, 250000.00, 350000.00),
        ('2024-11', 630000.00, 255000.00, 375000.00),
        ('2024-12', 650000.00, 260000.00, 390000.00),
        ('2025-01', 670000.00, 265000.00, 405000.00),
        ('2025-02', 660000.00, 270000.00, 390000.00),
        ('2025-03', 690000.00, 275000.00, 415000.00)
    ]
    
    with engine.connect() as conn:
        # Clear existing data (optional)
        print("Clearing existing data...")
        conn.execute(text("DELETE FROM financial_agent_pl_reports"))
        conn.execute(text("DELETE FROM financial_agent_balancesheets"))
        conn.commit()
        
        # Insert P&L data
        print("Inserting P&L data...")
        pl_insert_sql = """
        INSERT INTO financial_agent_pl_reports (month, revenue, cost_of_goods_sold, operating_expenses, net_profit)
        VALUES (:month, :revenue, :cost_of_goods_sold, :operating_expenses, :net_profit)
        """
        
        for month, revenue, cogs, op_exp, net_profit in pl_data:
            conn.execute(text(pl_insert_sql), {
                'month': month,
                'revenue': revenue,
                'cost_of_goods_sold': cogs,
                'operating_expenses': op_exp,
                'net_profit': net_profit
            })
        
        # Insert Balance Sheet data
        print("Inserting Balance Sheet data...")
        bs_insert_sql = """
        INSERT INTO financial_agent_balancesheets (month, total_assets, total_liabilities, equity)
        VALUES (:month, :total_assets, :total_liabilities, :equity)
        """
        
        for month, assets, liabilities, equity in bs_data:
            conn.execute(text(bs_insert_sql), {
                'month': month,
                'total_assets': assets,
                'total_liabilities': liabilities,
                'equity': equity
            })
        
        conn.commit()
        print("Sample data inserted successfully!")

def verify_data(engine):
    """Verify the inserted data."""
    
    with engine.connect() as conn:
        # Count records
        pl_count = conn.execute(text("SELECT COUNT(*) FROM financial_agent_pl_reports")).fetchone()[0]
        bs_count = conn.execute(text("SELECT COUNT(*) FROM financial_agent_balancesheets")).fetchone()[0]
        
        print(f"\nData Summary:")
        print(f"   P&L Reports: {pl_count} records")
        print(f"   Balance Sheets: {bs_count} records")
        
        # Show sample records
        print(f"\nSample P&L Data:")
        sample_pl = conn.execute(text("""
            SELECT month, revenue, net_profit 
            FROM financial_agent_pl_reports 
            ORDER BY month 
            LIMIT 3
        """)).fetchall()
        
        for row in sample_pl:
            print(f"   {row[0]}: Revenue=${row[1]:,.2f}, Net Profit=${row[2]:,.2f}")
        
        print(f"\nSample Balance Sheet Data:")
        sample_bs = conn.execute(text("""
            SELECT month, total_assets, equity 
            FROM financial_agent_balancesheets 
            ORDER BY month 
            LIMIT 3
        """)).fetchall()
        
        for row in sample_bs:
            print(f"   {row[0]}: Assets=${row[1]:,.2f}, Equity=${row[2]:,.2f}")

def main():
    """Main function to set up database with sample data."""
    
    print(" Financial Data Setup")
    print("=" * 40)
    
    try:
        # Connect to database
        print(" Connecting to database...")
        engine = get_database_connection()
        
        # Test connection
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).fetchone()[0]
            print(f" Connected to: {version[:30]}...")
        
        # Create tables
        print("\n  Creating tables...")
        create_tables(engine)
        
        # Insert sample data
        print("\n Inserting sample data...")
        insert_sample_data(engine)
        
        # Verify data
        verify_data(engine)
        
        print("\n Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Test with: python test.py")
        print("3. Try queries like:")
        print("   - 'What was the revenue last month?'")
        print("   - 'Show me profit for the last quarter'")
        print("   - 'What are my total assets?'")
        
    except Exception as e:
        print(f"\n Setup failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct database credentials")
        print("2. Ensure database is accessible")
        print("3. Make sure you have the required Python packages installed")

if __name__ == "__main__":
    main()
