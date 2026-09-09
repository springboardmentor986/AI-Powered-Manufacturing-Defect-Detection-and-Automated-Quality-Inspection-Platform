import io
import sys
import unittest
from pathlib import Path
from uuid import uuid4
from PIL import Image as PILImage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from app.database.connection import SessionLocal
from app.models.user import User
from app.models.image import Image as DBImage
from app.security.roles import SUPERVISOR_REGISTRATION_CODE
from tests.asgi_client import ASGITestClient
from ai.models.inspection_pipeline import InspectionPipeline

AI_DIR = PROJECT_ROOT / "ai"


class TestMilestone2Comprehensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ASGITestClient(app)
        unique_suffix = uuid4().hex[:8]

        cls.qe_email = f"qe_m2_{unique_suffix}@example.com"
        cls.qe_password = "QualityEngineer@2026"
        cls.qe_name = f"Quality Engineer {unique_suffix}"

        cls.sup_email = f"sup_m2_{unique_suffix}@example.com"
        cls.sup_password = "Supervisor@2026"
        cls.sup_name = f"Supervisor {unique_suffix}"

        cls.qe_token = None
        cls.sup_token = None
        cls.normal_image_id = None
        cls.defective_image_id = None

        # Instantiate pipeline for standalone verification
        cls.pipeline = InspectionPipeline(
            normal_features_path=str(AI_DIR / "models/normal_features_layer3.pt"),
            confidence_scores_path=str(AI_DIR / "evaluation/confidence_scores.csv"),
            size_boundaries_path=str(AI_DIR / "models/size_score_boundaries.csv"),
            segmentation_model_path=str(AI_DIR / "models/defect_segmenter_unet.pt"),
            segmentation_threshold_path=str(AI_DIR / "models/segmentation_threshold.txt"),
            anomaly_thresholds_path=str(AI_DIR / "models/anomaly_thresholds.csv"),
            postprocessing_config_path=str(AI_DIR / "models/segmentation_postprocessing.json"),
        )

    # -------------------------------------------------------------
    # PHASE 2: BACKEND & AUTHENTICATION TESTS
    # -------------------------------------------------------------
    def test_01_root_health_check(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VisionInspect AI Backend Running", resp.json()["message"])

    def test_02_register_qe_success(self):
        payload = {
            "name": self.qe_name,
            "email": self.qe_email,
            "password": self.qe_password,
            "role_id": 1,
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["email"], self.qe_email)
        self.assertEqual(data["role"], "Quality Engineer")

    def test_03_register_supervisor_without_code_fails(self):
        payload = {
            "name": "Invalid Sup",
            "email": f"sup_no_code_{uuid4().hex[:6]}@example.com",
            "password": "Password@123",
            "role_id": 2,
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_04_register_supervisor_with_invalid_code_fails(self):
        payload = {
            "name": "Invalid Sup Code",
            "email": f"sup_bad_code_{uuid4().hex[:6]}@example.com",
            "password": "Password@123",
            "role_id": 2,
            "supervisor_registration_code": "WRONG-CODE-XYZ",
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_05_register_supervisor_with_valid_code_success(self):
        payload = {
            "name": self.sup_name,
            "email": self.sup_email,
            "password": self.sup_password,
            "role_id": 2,
            "supervisor_registration_code": SUPERVISOR_REGISTRATION_CODE,
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["role"], "Factory Supervisor")

    def test_06_register_duplicate_email_fails(self):
        payload = {
            "name": "Duplicate User",
            "email": self.qe_email,
            "password": "Password@123",
            "role_id": 1,
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_07_register_invalid_role_id_fails(self):
        payload = {
            "name": "Invalid Role User",
            "email": f"bad_role_{uuid4().hex[:6]}@example.com",
            "password": "Password@123",
            "role_id": 99,
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertIn(resp.status_code, [400, 422])

    def test_08_register_weak_password_fails(self):
        payload = {
            "name": "Weak Pass",
            "email": f"weak_{uuid4().hex[:6]}@example.com",
            "password": "123",
            "role_id": 1,
        }
        resp = self.client.post("/auth/register", json=payload)
        self.assertEqual(resp.status_code, 422)

    def test_09_login_qe_success(self):
        resp = self.client.post(
            "/auth/login",
            json={"email": self.qe_email, "password": self.qe_password},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.__class__.qe_token = data["access_token"]

    def test_10_login_supervisor_success(self):
        resp = self.client.post(
            "/auth/login",
            json={"email": self.sup_email, "password": self.sup_password},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.__class__.sup_token = data["access_token"]

    def test_11_login_invalid_password_fails(self):
        resp = self.client.post(
            "/auth/login",
            json={"email": self.qe_email, "password": "WrongPassword123!"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_12_login_nonexistent_email_fails(self):
        resp = self.client.post(
            "/auth/login",
            json={"email": "nonexistent_user_999@example.com", "password": "Password@123"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_13_auth_me_qe(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}
        resp = self.client.get("/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], self.qe_email)
        self.assertEqual(resp.json()["role_id"], 1)

    def test_14_auth_me_supervisor(self):
        headers = {"Authorization": f"Bearer {self.sup_token}"}
        resp = self.client.get("/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["email"], self.sup_email)
        self.assertEqual(resp.json()["role_id"], 2)

    def test_15_auth_missing_token_fails(self):
        resp = self.client.get("/auth/me")
        self.assertIn(resp.status_code, [401, 403])

    def test_16_auth_invalid_token_fails(self):
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        resp = self.client.get("/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 401)

    # -------------------------------------------------------------
    # PHASE 2 & 3: IMAGE UPLOAD & ROLE AUTHORIZATION TESTS
    # -------------------------------------------------------------
    def test_17_qe_upload_valid_png(self):
        img_byte_arr = io.BytesIO()
        image = PILImage.new("RGB", (100, 100), color=(100, 150, 200))
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        headers = {"Authorization": f"Bearer {self.qe_token}"}
        files = {"file": ("test_valid.png", img_byte_arr, "image/png")}
        resp = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("id", data)
        self.assertEqual(data["original_filename"], "test_valid.png")

        # Verify inspection_status via GET /images/{id}
        get_resp = self.client.get(f"/images/{data['id']}", headers=headers)
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["inspection_status"], "pending")

    def test_18_qe_upload_valid_jpeg(self):
        img_byte_arr = io.BytesIO()
        image = PILImage.new("RGB", (100, 100), color=(200, 150, 100))
        image.save(img_byte_arr, format="JPEG")
        img_byte_arr.seek(0)

        headers = {"Authorization": f"Bearer {self.qe_token}"}
        files = {"file": ("test_valid.jpg", img_byte_arr, "image/jpeg")}
        resp = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("id", data)

    def test_19_upload_invalid_file_type_fails(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}
        files = {"file": ("script.sh", b"#!/bin/bash\necho hello", "text/plain")}
        resp = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(resp.status_code, 400)

    def test_20_upload_corrupted_non_image_fails(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}
        files = {"file": ("corrupted.png", b"NOT_A_REAL_PNG_IMAGE_BYTES_XYZ", "image/png")}
        resp = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(resp.status_code, 400)

    def test_21_supervisor_cannot_upload(self):
        img_byte_arr = io.BytesIO()
        image = PILImage.new("RGB", (50, 50), color="blue")
        image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        headers = {"Authorization": f"Bearer {self.sup_token}"}
        files = {"file": ("sup_upload.png", img_byte_arr, "image/png")}
        resp = self.client.post("/images/upload", headers=headers, files=files)
        self.assertEqual(resp.status_code, 403)

    def test_22_both_roles_can_list_images(self):
        qe_headers = {"Authorization": f"Bearer {self.qe_token}"}
        sup_headers = {"Authorization": f"Bearer {self.sup_token}"}
        r1 = self.client.get("/images/", headers=qe_headers)
        r2 = self.client.get("/images/", headers=sup_headers)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertGreaterEqual(len(r1.json()), 1)

    def test_23_supervisor_access_review_queue(self):
        sup_headers = {"Authorization": f"Bearer {self.sup_token}"}
        resp = self.client.get("/images/supervisor/review-queue", headers=sup_headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_24_qe_cannot_access_review_queue(self):
        qe_headers = {"Authorization": f"Bearer {self.qe_token}"}
        resp = self.client.get("/images/supervisor/review-queue", headers=qe_headers)
        self.assertEqual(resp.status_code, 403)

    # -------------------------------------------------------------
    # PHASE 4 & 5: AI PIPELINE & OUTPUT CONSISTENCY TESTS
    # -------------------------------------------------------------
    def test_25_normal_specimen_inspection_and_invariants(self):
        carpet_good = PROJECT_ROOT / "mvtec_anomaly_detection/carpet/test/good/000.png"
        self.assertTrue(carpet_good.exists())

        headers = {"Authorization": f"Bearer {self.qe_token}"}
        with open(carpet_good, "rb") as f:
            resp = self.client.post(
                "/images/upload",
                headers=headers,
                files={"file": ("carpet_good.png", f.read(), "image/png")},
            )
        self.assertEqual(resp.status_code, 200)
        img_id = resp.json()["id"]
        self.__class__.normal_image_id = img_id

        # Inspect without labels (Pure Automatic)
        insp_resp = self.client.post(f"/images/{img_id}/inspect", headers=headers, json={})
        self.assertEqual(insp_resp.status_code, 200)
        data = insp_resp.json()

        # Invariant Assertions
        self.assertEqual(data["category"], "carpet")
        self.assertEqual(data["defect_type"], "normal")
        self.assertEqual(data["resolved_defect_status"], "normal")
        self.assertEqual(data["inspection_decision"], "NORMAL")
        self.assertEqual(data["quality_decision"], "Accept")
        self.assertEqual(data["severity_level"], "Low")
        self.assertEqual(data["severity_score"], 0.0)
        self.assertEqual(data["size_score"], 0.0)
        self.assertEqual(data["location_score"], 0.0)
        self.assertEqual(data["defect_type_score"], 0.0)
        self.assertEqual(data["confidence_score"], 0.0)
        self.assertEqual(data["predicted_area_percent"], 0.0)

    def test_26_defective_specimen_inspection_and_invariants(self):
        bottle_defective = PROJECT_ROOT / "mvtec_anomaly_detection/bottle/test/broken_large/000.png"
        self.assertTrue(bottle_defective.exists())

        headers = {"Authorization": f"Bearer {self.qe_token}"}
        with open(bottle_defective, "rb") as f:
            resp = self.client.post(
                "/images/upload",
                headers=headers,
                files={"file": ("bottle_broken.png", f.read(), "image/png")},
            )
        self.assertEqual(resp.status_code, 200)
        img_id = resp.json()["id"]
        self.__class__.defective_image_id = img_id

        # Inspect without labels
        insp_resp = self.client.post(f"/images/{img_id}/inspect", headers=headers, json={})
        self.assertEqual(insp_resp.status_code, 200)
        data = insp_resp.json()

        # Defective Invariant Assertions
        self.assertEqual(data["category"], "bottle")
        self.assertEqual(data["defect_type"], "broken_large")
        self.assertEqual(data["inspection_decision"], "DEFECTIVE")
        self.assertEqual(data["quality_decision"], "Reject")
        self.assertGreater(data["severity_score"], 40.0)
        self.assertGreater(data["predicted_area_percent"], 0.0)

        # Exact 30/25/25/20 Formula Verification
        expected_sev = (
            data["size_score"] * 0.30
            + data["location_score"] * 0.25
            + data["defect_type_score"] * 0.25
            + data["confidence_score"] * 0.20
        )
        self.assertAlmostEqual(data["severity_score"], expected_sev, places=2)

    def test_27_inspection_overlay_endpoints(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}

        # Normal overlay retrieval
        resp_norm = self.client.get(
            f"/images/{self.normal_image_id}/inspection-overlay",
            headers=headers,
        )
        self.assertEqual(resp_norm.status_code, 200)
        self.assertEqual(resp_norm.headers["content-type"], "image/png")

        # Defective overlay retrieval
        resp_def = self.client.get(
            f"/images/{self.defective_image_id}/inspection-overlay",
            headers=headers,
        )
        self.assertEqual(resp_def.status_code, 200)
        self.assertEqual(resp_def.headers["content-type"], "image/png")

    # -------------------------------------------------------------
    # PHASE 3: DATABASE PERSISTENCE & LIFECYCLE
    # -------------------------------------------------------------
    def test_28_database_persistence_verification(self):
        db = SessionLocal()
        try:
            # Check user record
            qe_user = db.query(User).filter(User.email == self.qe_email).first()
            self.assertIsNotNone(qe_user)
            self.assertEqual(qe_user.role_id, 1)
            self.assertTrue(qe_user.password_hash.startswith("$argon2"))

            # Check inspected image record
            img = db.query(DBImage).filter(DBImage.id == self.defective_image_id).first()
            self.assertIsNotNone(img)
            self.assertEqual(img.inspection_status, "completed")
            self.assertEqual(img.category, "bottle")
            self.assertEqual(img.defect_type, "broken_large")
            self.assertEqual(img.quality_decision, "Reject")
        finally:
            db.close()

    # -------------------------------------------------------------
    # PHASE 2 & 7: SUPERVISOR REVIEW WORKFLOW (TEST C)
    # -------------------------------------------------------------
    def test_29_supervisor_review_approve_and_reject(self):
        sup_headers = {"Authorization": f"Bearer {self.sup_token}"}

        # Review defective image (Reject confirmation)
        payload = {
            "decision": "rejected",
            "notes": "Verified critical fracture on bottle wall. Production lot quarantined.",
        }
        resp = self.client.post(
            f"/images/{self.defective_image_id}/review",
            headers=sup_headers,
            json=payload,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["inspection_status"], "reviewed")
        self.assertEqual(data["supervisor_decision"], "rejected")
        self.assertIn("Production lot quarantined", data["supervisor_notes"])
        self.assertIsNotNone(data["reviewed_by"])
        self.assertEqual(data["reviewed_by"]["email"], self.sup_email)

    def test_30_qe_cannot_review(self):
        qe_headers = {"Authorization": f"Bearer {self.qe_token}"}
        payload = {"decision": "approved", "notes": "Unauthorized QE attempt"}
        resp = self.client.post(
            f"/images/{self.defective_image_id}/review",
            headers=qe_headers,
            json=payload,
        )
        self.assertEqual(resp.status_code, 403)

    def test_31_analytics_summary_endpoint(self):
        headers = {"Authorization": f"Bearer {self.qe_token}"}
        resp = self.client.get("/analytics/summary", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_inspections", data)
        self.assertIn("accepted", data)
        self.assertIn("rejected", data)


if __name__ == "__main__":
    unittest.main()
