from app.core.config import settings


ROLE_QUALITY_ENGINEER = 1
ROLE_FACTORY_SUPERVISOR = 2

SUPPORTED_ROLE_IDS = {
    ROLE_QUALITY_ENGINEER,
    ROLE_FACTORY_SUPERVISOR,
}

ROLE_NAMES = {
    ROLE_QUALITY_ENGINEER: "Quality Engineer",
    ROLE_FACTORY_SUPERVISOR: "Factory Supervisor",
}

SUPERVISOR_REGISTRATION_CODE = settings.supervisor_registration_code