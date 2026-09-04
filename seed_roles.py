from backend.app.core.database import SessionLocal
from backend.app.models.role import Role


db = SessionLocal()

try:
    roles = [
        {
            "name": "Admin",
            "description": "System administrator with full access"
        },
        {
            "name": "Quality Engineer",
            "description": "Performs product quality inspections"
        },
        {
            "name": "Factory Supervisor",
            "description": "Monitors production and inspection operations"
        }
    ]

    for role_data in roles:
        existing_role = (
            db.query(Role)
            .filter(Role.name == role_data["name"])
            .first()
        )

        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"]
            )

            db.add(role)

    db.commit()

    print("Initial roles added successfully!")

finally:
    db.close()