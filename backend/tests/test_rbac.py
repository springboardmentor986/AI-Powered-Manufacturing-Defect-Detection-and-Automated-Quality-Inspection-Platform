import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from auth import require_inspector, require_supervisor, require_admin



def test_auth_token_schema_and_role():
    from schemas import TokenResponse
    token_resp = TokenResponse(access_token="test-token", token_type="bearer", role="admin")
    assert token_resp.access_token == "test-token"
    assert token_resp.role == "admin"
    assert token_resp.token_type == "bearer"


def test_role_dependencies():
    class DummyUser:
        def __init__(self, role):
            self.role = role

    inspector = DummyUser("inspector")
    supervisor = DummyUser("supervisor")
    admin = DummyUser("admin")

    # Inspector check
    assert require_inspector(inspector).role == "inspector"
    assert require_inspector(supervisor).role == "supervisor"
    assert require_inspector(admin).role == "admin"

    # Supervisor check
    with pytest.raises(Exception):
        require_supervisor(inspector)
    assert require_supervisor(supervisor).role == "supervisor"
    assert require_supervisor(admin).role == "admin"

    # Admin check
    with pytest.raises(Exception):
        require_admin(inspector)
    with pytest.raises(Exception):
        require_admin(supervisor)
    assert require_admin(admin).role == "admin"
