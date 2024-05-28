from sqlalchemy import inspect, text
from anomalyDetector.db.db import session, engine
from anomalyDetector.db.models import Base

def truncate_all_tables():
    # Get all table names
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    # Generate and execute TRUNCATE statements
    with session.begin():
        for table_name in table_names:
            session.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;'))

if __name__ == "__main__":
    truncate_all_tables()
    print("All tables truncated successfully.")

