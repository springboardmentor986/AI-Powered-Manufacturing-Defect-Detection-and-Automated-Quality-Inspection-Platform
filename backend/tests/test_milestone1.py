import io
import unittest
from uuid import uuid4
from PIL import Image as PILImage

from app.main import app
from app.security.roles import SUPERVISOR_REGISTRATION_CODE
from tests.asgi_client import ASGITestClient


class TestMilestone1FullWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)

        # Unique suffix for test users to avoid duplicate email collisions across runs
        unique_suffix = uuid4().hex[:8]
        cls.qe_email = f"qe_{unique_suffix}@example.com"
        cls.qe_password = "QualityEngineer@2026"
        cls.qe_name = f"Quality Engineer {unique_suffix}"

        cls.sup_email = f"sup_{unique_suffix}@example.com"
        cls.sup_password = "Supervisor@2026"
        cls.sup_name = f"Supervisor {unique_suffix}"

        cls.qe_token = None
        cls.sup_token = None
        cls.uploaded_image_id = None

    def test_01_root_health_check(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("VisionInspect AI Backend Running", response.json()["message"])

    def test_02_register_quality_engineer_success(self):
        payload = {
            "name": self.qe_name,
            "email": self.qe_email,
            "password": self.qe_password,
            "role_id": 1,
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["email"], self.qe_email)
        self.assertEqual(data["role_id"], 1)
        self.assertEqual(data["role"], "Quality Engineer")
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_03_register_supervisor_without_code_fails(self):
        payload = {
            "name": "Unauthorized Supervisor",
            "email": f"fake_sup_{uuid4().hex[:6]}@example.com",
            "password": "Password@123",
            "role_id": 2,
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("supervisor registration code", response.json()["detail"].lower())

    def test_04_register_supervisor_with_invalid_code_fails(self):
        payload = {
            "name": "Invalid Code Supervisor",
            "email": f"fake_sup_{uuid4().hex[:6]}@example.com",
            "password": "Password@123",
            "role_id": 2,
            "supervisor_registration_code": "WRONG-CODE-999",
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("supervisor registration code", response.json()["detail"].lower())

    def test_05_register_supervisor_with_valid_code_success(self):
        payload = {
            "name": self.sup_name,
            "email": self.sup_email,
            "password": self.sup_password,
            "role_id": 2,
            "supervisor_registration_code": SUPERVISOR_REGISTRATION_CODE,
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["email"], self.sup_email)
        self.assertEqual(data["role_id"], 2)
        self.assertEqual(data["role"], "Factory Supervisor")
        self.assertNotIn("password", data)
        self.assertNotIn("password_hash", data)

    def test_06_register_duplicate_email_fails(self):
        payload = {
            "name": "Duplicate User",
            "email": self.qe_email,
            "password": "Password@123",
            "role_id": 1,
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("email already exists", response.json()["detail"].lower())

    def test_07_register_invalid_role_id_fails(self):
        payload = {
            "name": "Hacker User",
            "email": f"hacker_{uuid4().hex[:6]}@example.com",
            "password": "Password@123",
            "role_id": 99,
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertIn(response.status_code, [400, 422])

    def test_08_register_weak_password_fails(self):
        payload = {
            "name": "Weak Pass User",
            "email": f"weak_{uuid4().hex[:6]}@example.com",
            "password": "simplepassword",
            "role_id": 1,
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_09_login_quality_engineer(self):
        response = self.client.post(
            "/auth/login",
            json={"email": self.qe_email, "password": self.qe_password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role_id"], 1)
        self.assertEqual(data["user"]["role"], "Quality Engineer")
        self.__class__.qe_token = data["access_token"]

    def test_10_login_factory_supervisor(self):
        response = self.client.post(
            "/auth/login",
            json={"email": self.sup_email, "password": self.sup_password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["role_id"], 2)
        self.assertEqual(data["user"]["role"], "Factory Supervisor")
        self.__class__.sup_token = data["access_token"]

    def test_12_get_current_user_me(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}
        response = self.client.get("/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.qe_email)
        self.assertEqual(data["role_id"], 1)

    def test_13_qe_upload_image_success(self):
        # Generate dummy PNG in memory
        img_byte_arr = io.BytesIO()
        image = PILImage.new("RGB", (100, 100), color=(73, 109, 137))
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        headers = {"Authorization": f"Bearer {self.qe_token}"}
        files = {"file": ("inspection_sample.png", img_byte_arr, "image/png")}

        response = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["original_filename"], "inspection_sample.png")
        self.__class__.uploaded_image_id = data["id"]

    def test_14_supervisor_cannot_upload_image(self):
        img_byte_arr = io.BytesIO()
        image = PILImage.new("RGB", (50, 50), color="red")
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        headers = {"Authorization": f"Bearer {self.sup_token}"}
        files = {"file": ("sup_upload.png", img_byte_arr, "image/png")}

        response = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(response.status_code, 403)
        self.assertIn("permission", response.json()["detail"].lower())

    def test_15_both_roles_can_view_images(self):
        qe_headers = {"Authorization": f"Bearer {self.qe_token}"}
        sup_headers = {"Authorization": f"Bearer {self.sup_token}"}

        resp1 = self.client.get("/images/", headers=qe_headers)
        self.assertEqual(resp1.status_code, 200)
        self.assertGreaterEqual(len(resp1.json()), 1)

        resp2 = self.client.get("/images/", headers=sup_headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertGreaterEqual(len(resp2.json()), 1)

    def test_16_supervisor_can_access_review_queue(self):
        sup_headers = {"Authorization": f"Bearer {self.sup_token}"}
        response = self.client.get("/images/supervisor/review-queue", headers=sup_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_17_qe_cannot_access_supervisor_review_queue(self):
        qe_headers = {"Authorization": f"Bearer {self.qe_token}"}
        response = self.client.get("/images/supervisor/review-queue", headers=qe_headers)
        self.assertEqual(response.status_code, 403)

    def test_18_supervisor_can_review_image(self):
        sup_headers = {"Authorization": f"Bearer {self.sup_token}"}
        payload = {
            "decision": "approved",
            "notes": "Component surface meets ISO inspection tolerances.",
        }
        response = self.client.post(
            f"/images/{self.uploaded_image_id}/review",
            headers=sup_headers,
            json=payload,
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["inspection_status"], "reviewed")
        self.assertEqual(data["supervisor_decision"], "approved")
        self.assertEqual(
            data["supervisor_notes"],
            "Component surface meets ISO inspection tolerances.",
        )
        self.assertIsNotNone(data["reviewed_by"])
        self.assertEqual(data["reviewed_by"]["name"], self.sup_name)

    def test_19_qe_cannot_review_image(self):
        qe_headers = {"Authorization": f"Bearer {self.qe_token}"}
        payload = {
            "decision": "rejected",
            "notes": "Attempting unauthorized QE review.",
        }
        response = self.client.post(
            f"/images/{self.uploaded_image_id}/review",
            headers=qe_headers,
            json=payload,
        )
        self.assertEqual(response.status_code, 403)

    def test_20_protected_image_file_download(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}
        response = self.client.get(
            f"/images/{self.uploaded_image_id}/file",
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/png")

    def test_21_unauthenticated_requests_fail(self):
        # Missing token
        r1 = self.client.get("/auth/me")
        self.assertIn(r1.status_code, [401, 403])

        # Invalid token
        r2 = self.client.get("/images/", headers={"Authorization": "Bearer invalid.token.value"})
        self.assertEqual(r2.status_code, 401)


if __name__ == "__main__":
    unittest.main()
