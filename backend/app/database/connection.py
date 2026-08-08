from sqlmodel import SQLModel, create_engine, Session
from app.config.settings import settings
from app.utils.logger import logger

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def init_db():
    logger.info("Initializing database tables...")
    import app.models  # Ensure all SQLModel models are registered
    SQLModel.metadata.create_all(engine)
    
    # Auto-migrate missing columns for existing SQLite tables
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table_name, table in SQLModel.metadata.tables.items():
            if inspector.has_table(table_name):
                existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                for column in table.columns:
                    if column.name not in existing_cols:
                        col_type = column.type.compile(engine.dialect)
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"
                        try:
                            conn.execute(text(sql))
                            logger.info(f"Added missing column '{column.name}' to table '{table_name}'.")
                        except Exception as e:
                            logger.warning(f"Could not add column '{column.name}' to '{table_name}': {e}")
    logger.info("Database tables initialized successfully.")

def get_session():
    with Session(engine) as session:
        yield session
