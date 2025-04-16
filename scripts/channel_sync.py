import pandas as pd
from telethon import TelegramClient
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import asyncio
from datetime import datetime
from helper.config_manager import ConfigManager
from helper.Logger import Logging

async def sync_telegram_channels(config_path="config/demo_config.yaml", log_file="logs/app.log"):
    """Sync Telegram channel data with Postgres database."""
    # Initialize config and logger
    config_manager = ConfigManager(config_file=config_path)
    logger = Logging(config=config_manager, instance_id="channel_sync")
    logger.set_log_file("channel_sync")

    try:
        # Extract config values
        db_config = config_manager.get_section("database")
        tele_config = config_manager.get_section("telegram")
        logger.info("Starting Telegram channel sync")

        # Setup database engine
        connection_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        engine = create_engine(connection_string)

        # Test connection
        with engine.connect() as conn:
            logger.info(f"Connected to Postgres database: {db_config['database']}")

        # Telegram client
        client = TelegramClient(tele_config["session_path"], tele_config["api_id"], tele_config["api_hash"])
        await client.connect()
        if not await client.is_user_authorized():
            logger.info("Session not authorized; starting login")
            await client.start(phone=tele_config["phone_number"])
        else:
            logger.info("Using existing authorized session")

        # Fetch channels
        dialogs = await client.get_dialogs()
        channel_data = [(dialog.id, dialog.name) for dialog in dialogs if dialog.is_channel]
        df_tele = pd.DataFrame(channel_data, columns=['ID', 'Name'])
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE temp_channels"))
            df_tele.to_sql('temp_channels', conn, if_exists='append', index=False)
            conn.commit()
            logger.info(f"Stored {len(df_tele)} channels in temp_channels")

        # Fetch DB channels
        with engine.connect() as conn:
            query = "SELECT ID, Name, Operating, Disappeared, created_dt, update_dt FROM channels"
            df_db = pd.read_sql(query, conn)
            logger.info(f"Fetched {len(df_db)} channels from database")

        # Update channels table
        if df_db.empty or df_tele.empty:
            logger.warning("Cannot update channels: database or Telegram data missing")
        else:
            df_db.set_index('ID', inplace=True)
            df_tele.set_index('ID', inplace=True)
            with engine.connect() as conn:
                new_channels = df_tele[~df_tele.index.isin(df_db.index)].copy()
                if not new_channels.empty:
                    new_channels['Operating'] = 0
                    new_channels['Disappeared'] = 0
                    new_channels['created_dt'] = datetime.now()
                    new_channels['update_dt'] = None
                    new_channels.reset_index().to_sql('channels', conn, if_exists='append', index=False)
                    logger.info(f"Inserted {len(new_channels)} new channels")
                for channel_id in df_db.index:
                    if channel_id in df_tele.index:
                        tele_name = df_tele.loc[channel_id, 'Name']
                        db_name = df_db.loc[channel_id, 'Name']
                        db_disappeared = df_db.loc[channel_id, 'Disappeared']
                        update_needed = (tele_name != db_name) or (db_disappeared != 0)
                        if update_needed:
                            conn.execute(
                                text("UPDATE channels SET Name = :name, Disappeared = 0, update_dt = :update_dt WHERE ID = :id"),
                                {"name": tele_name, "update_dt": datetime.now(), "id": channel_id}
                            )
                    else:
                        if df_db.loc[channel_id, 'Disappeared'] != 1:
                            conn.execute(
                                text("UPDATE channels SET Disappeared = 1, update_dt = :update_dt WHERE ID = :id"),
                                {"update_dt": datetime.now(), "id": channel_id}
                            )
                conn.commit()
                logger.info("Channels table updated successfully")

    except Exception as e:
        logger.error(f"Error syncing channels: {e}")
    finally:
        if 'client' in locals() and client.is_connected():
            await client.disconnect()
            logger.info("Disconnected from Telegram")
        logger.close_log()

def run_sync():
    """Wrapper for ProcessManager to run sync_telegram_channels."""
    asyncio.run(sync_telegram_channels())