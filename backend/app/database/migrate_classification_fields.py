from sqlalchemy import text
from app.database.connection import engine


def migrate_images_table():
    """
    Safely adds predicted_category, predicted_defect_type, and classification_confidence
    columns to the images table if they do not already exist.
    """
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE images ADD COLUMN IF NOT EXISTS predicted_category VARCHAR;")
        )
        connection.execute(
            text("ALTER TABLE images ADD COLUMN IF NOT EXISTS predicted_defect_type VARCHAR;")
        )
        connection.execute(
            text("ALTER TABLE images ADD COLUMN IF NOT EXISTS resolved_defect_status VARCHAR;")
        )
        connection.execute(
            text("ALTER TABLE images ADD COLUMN IF NOT EXISTS classification_confidence VARCHAR;")
        )
    print("Database migration successful: classification and decision columns added or verified.")


if __name__ == "__main__":
    migrate_images_table()
