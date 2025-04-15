import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Set DATABASE_URL explicitly
os.environ['DATABASE_URL'] = 'postgres://u64g8eocr7nhul:p3b8ecfc9a637f11fb55f26fcf499d36f5f6a5c90a59f1c99a40fce32e4b549b7@ca932070ke6bv1.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/da1co8rkl4afh'
print(f"Set DATABASE_URL: {os.environ.get('DATABASE_URL')}")  # Debug

from sqlalchemy.sql import text
from helper.config_manager import ConfigManager
from helper.Logger import Logging
from helper.database import DatabaseHandler
from helper.timezone import get_formatted_timestamp

def demo_crud_operations():
    # Initialize helpers
    config = ConfigManager("config/demo_config.yaml")
    print(f"Database config: {config.get_section('database')}")  # Debug
    logger = Logging(config, instance_id="demo_relations")
    db_handler = DatabaseHandler(config, logger)
    engine = db_handler.get_engine()

    with engine.connect() as conn:
        # Create: Insert a new trader and profile
        logger.info("Creating a new trader and profile")
        trader_result = conn.execute(text("""
            INSERT INTO traders (name, email)
            VALUES (:name, :email)
            RETURNING trader_id
        """), {"name": "David Wilson", "email": "david@trading.com"})
        trader_id = trader_result.fetchone()[0]
        
        conn.execute(text("""
            INSERT INTO profiles (trader_id, bio, risk_level)
            VALUES (:trader_id, :bio, :risk_level)
        """), {
            "trader_id": trader_id,
            "bio": "Day trader specializing in stocks",
            "risk_level": "Medium"
        })

        # Create: Insert a trade for the new trader with tags
        trade_result = conn.execute(text("""
            INSERT INTO trades (trader_id, symbol, amount, trade_date)
            VALUES (:trader_id, :symbol, :amount, :trade_date)
            RETURNING trade_id
        """), {
            "trader_id": trader_id,
            "symbol": "GOOGL",
            "amount": 2500.00,
            "trade_date": "2025-04-14T14:00:00+00:00"
        })
        trade_id = trade_result.fetchone()[0]

        # Link trade to tags (Stock, Long)
        conn.execute(text("""
            INSERT INTO trade_tags (trade_id, tag_id)
            VALUES (:trade_id, (SELECT tag_id FROM tags WHERE name = 'Stock')),
                   (:trade_id, (SELECT tag_id FROM tags WHERE name = 'Long'))
        """), {"trade_id": trade_id})

        # Read: Query trader with profile, trades, and tags
        logger.info("Reading trader data with relations")
        result = conn.execute(text("""
            SELECT t.trader_id, t.name, p.bio, p.risk_level,
                   tr.trade_id, tr.symbol, tr.amount, tr.trade_date,
                   tg.name AS tag_name
            FROM traders t
            LEFT JOIN profiles p ON t.trader_id = p.trader_id
            LEFT JOIN trades tr ON t.trader_id = tr.trader_id
            LEFT JOIN trade_tags tt ON tr.trade_id = tt.trade_id
            LEFT JOIN tags tg ON tt.tag_id = tg.tag_id
            WHERE t.email = :email
        """), {"email": "david@trading.com"})
        rows = result.fetchall()
        for row in rows:
            logger.info(f"Trader: {row.name}, Bio: {row.bio}, Trade: {row.symbol}, Tags: {row.tag_name}")

        # Update: Update trader's profile risk level
        logger.info("Updating trader's risk level")
        conn.execute(text("""
            UPDATE profiles
            SET risk_level = :risk_level
            WHERE trader_id = :trader_id
        """), {"risk_level": "High", "trader_id": trader_id})

        # Delete: Delete the trade (cascades to trade_tags)
        logger.info("Deleting the trade")
        conn.execute(text("DELETE FROM trades WHERE trade_id = :trade_id"), {"trade_id": trade_id})

        conn.commit()
        logger.info("CRUD operations completed")

if __name__ == "__main__":
    demo_crud_operations()