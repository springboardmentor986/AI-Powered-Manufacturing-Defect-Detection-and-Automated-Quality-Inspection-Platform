import sqlite3
from pathlib import Path


# ============================================================
# VISIONINSPECT AI
# DATABASE MODULE
# ============================================================


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_NAME = BASE_DIR / "visioninspect.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        str(DATABASE_NAME)
    )

    connection.row_factory = sqlite3.Row

    return connection


# ------------------------------------------------------------
# Compatibility function
# main.py uses get_db_connection()
# ------------------------------------------------------------

def get_db_connection():

    return get_connection()


# ============================================================
# CREATE TABLES
# ============================================================

def create_tables():

    connection = get_connection()

    cursor = connection.cursor()


    # ========================================================
    # USERS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL

        )
    """)


    # ========================================================
    # INSPECTIONS TABLE
    # ========================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inspections (

            inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            image_name TEXT NOT NULL,

            upload_time TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            status TEXT NOT NULL,

            processed_path TEXT,

            anomaly_score REAL,

            quality_score REAL,

            final_decision TEXT,

            defect_type TEXT,

            defect_category TEXT,

            severity_score REAL,

            severity_level TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(user_id)

        )
    """)


    connection.commit()

    connection.close()


# ============================================================
# DATABASE MIGRATION
# ============================================================

def migrate_database():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # Get existing columns
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(inspections)"
    )

    rows = cursor.fetchall()


    existing_columns = {

        row["name"]

        for row in rows

    }


    # --------------------------------------------------------
    # Required AI columns
    # --------------------------------------------------------

    new_columns = {

        "anomaly_score": "REAL",

        "quality_score": "REAL",

        "final_decision": "TEXT",

        "defect_type": "TEXT",

        "defect_category": "TEXT",

        "severity_score": "REAL",

        "severity_level": "TEXT"

    }


    # --------------------------------------------------------
    # Add missing columns
    # --------------------------------------------------------

    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE inspections
                ADD COLUMN {column_name} {column_type}
                """
            )


    connection.commit()

    connection.close()


# ============================================================
# DEFAULT USERS
# ============================================================

def add_default_users():

    connection = get_connection()

    cursor = connection.cursor()


    users = [

        (
            "Admin User",
            "admin@visioninspect.ai",
            "admin123",
            "Quality Engineer"
        ),

        (
            "Factory Supervisor",
            "supervisor@visioninspect.ai",
            "super123",
            "Factory Supervisor"
        )

    ]


    # --------------------------------------------------------
    # Insert default users
    # --------------------------------------------------------

    for user in users:

        try:

            cursor.execute(
                """
                INSERT INTO users
                (
                    name,
                    email,
                    password,
                    role
                )

                VALUES (?, ?, ?, ?)
                """,

                user
            )

        except sqlite3.IntegrityError:

            # User already exists
            pass


    connection.commit()

    connection.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_db():

    print()

    print("=" * 60)

    print(
        "VISIONINSPECT AI - DATABASE INITIALIZATION"
    )

    print("=" * 60)


    print()

    print(
        f"Database: {DATABASE_NAME}"
    )


    # --------------------------------------------------------
    # Create tables
    # --------------------------------------------------------

    create_tables()

    print(
        "✓ Tables created / verified"
    )


    # --------------------------------------------------------
    # Migrate existing database
    # --------------------------------------------------------

    migrate_database()

    print(
        "✓ Database migration completed"
    )


    # --------------------------------------------------------
    # Add default users
    # --------------------------------------------------------

    add_default_users()

    print(
        "✓ Default users verified"
    )


    print()

    print(
        "✓ DATABASE READY"
    )

    print("=" * 60)

    print()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    init_db()