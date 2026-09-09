import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app
from tests.asgi_client import ASGITestClient


def test_automatic_inspection():
    client = ASGITestClient(app)

    # Login
    login_resp = client.post(
        "/auth/login",
        json={"email": "qe_test_eval@example.com", "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Test cases: pure automatic classification without providing category or defect_type
    test_cases = [
        {
            "name": "Automatic Cable Good",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "cable" / "train" / "good" / "004.png",
            "expected_category": "cable",
            "expected_defect": "normal",
            "expected_decision": "Accept",
        },
        {
            "name": "Automatic Cable Defective",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "cable" / "test" / "cut_inner_insulation" / "000.png",
            "expected_category": "cable",
            "expected_defect_sub": "cut",
            "expected_decision": "Reject",
        },
        {
            "name": "Automatic Hazelnut Defective (Crack)",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "hazelnut" / "test" / "crack" / "000.png",
            "expected_category": "hazelnut",
            "expected_defect": "crack",
            "expected_decision": "Reject",
        },
        {
            "name": "Automatic Bottle Defective (Broken Large)",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "bottle" / "test" / "broken_large" / "000.png",
            "expected_category": "bottle",
            "expected_defect": "broken_large",
            "expected_decision": "Reject",
        },
        {
            "name": "Automatic Tile Defective (Crack)",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "tile" / "test" / "crack" / "000.png",
            "expected_category": "tile",
            "expected_defect": "crack",
            "expected_decision": "Reject",
        },
        {
            "name": "Automatic Tile Good",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "tile" / "train" / "good" / "000.png",
            "expected_category": "tile",
            "expected_defect": "normal",
            "expected_decision": "Accept",
        },
    ]

    for tc in test_cases:
        img_p = tc["path"]
        with open(img_p, "rb") as f:
            file_bytes = f.read()

        # 1. Upload without category/defect
        upload_resp = client.post(
            "/images/upload",
            headers=headers,
            files={"file": (img_p.name, file_bytes, "image/png")},
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        image_id = upload_resp.json()["id"]

        # 2. Inspect with empty payload {}
        inspect_resp = client.post(
            f"/images/{image_id}/inspect",
            headers=headers,
            json={},  # Empty payload! Fully automatic
        )
        assert inspect_resp.status_code == 200, f"Inspect failed: {inspect_resp.text}"
        data = inspect_resp.json()

        print(f"[{tc['name']}] Category: {data['predicted_category']}, Defect: {data['predicted_defect_type']}, Decision: {data['quality_decision']}")

        # Verify predictions
        assert data["predicted_category"] == tc["expected_category"], f"Expected {tc['expected_category']}, got {data['predicted_category']}"
        assert data["category"] == tc["expected_category"]
        assert data["classification_confidence"] is not None and float(data["classification_confidence"]) > 0.0

        if "expected_defect" in tc:
            assert data["defect_type"] == tc["expected_defect"], f"Expected {tc['expected_defect']}, got {data['defect_type']}"
        elif "expected_defect_sub" in tc:
            assert tc["expected_defect_sub"] in data["defect_type"], f"Expected substring {tc['expected_defect_sub']}, got {data['defect_type']}"

        assert data["quality_decision"] == tc["expected_decision"], f"Expected {tc['expected_decision']}, got {data['quality_decision']}"

        # 3. Check /images/{id} GET serialization
        get_resp = client.get(f"/images/{image_id}", headers=headers)
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["predicted_category"] == tc["expected_category"]
        assert get_data["predicted_defect_type"] is not None
        assert get_data["classification_confidence"] is not None

    print("Automatic classification: 6/6 passed.")


if __name__ == "__main__":
    test_automatic_inspection()
