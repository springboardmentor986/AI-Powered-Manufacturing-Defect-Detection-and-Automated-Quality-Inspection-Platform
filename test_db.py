from sqlalchemy import text

from backend.app.core.database import engine


try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        print("PostgreSQL Connected Successfully!")
        print(result.fetchone()[0])

except Exception as e:
    print("Database Connection Failed!")
    print(e)