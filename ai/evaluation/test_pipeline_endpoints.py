import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from app.main import app
from tests.asgi_client import ASGITestClient


def run_endpoint_tests():
    client = ASGITestClient(app)

    # 1. Login as Quality Engineer
    login_resp = client.post(
        "/auth/login",
        json={"email": "qe_test_eval@example.com", "password": "Password123!"},
    )

    if login_resp.status_code != 200:
        # Register a test QE account
        reg_resp = client.post(
            "/auth/register",
            json={
                "name": "QE Evaluation User",
                "email": "qe_test_eval@example.com",
                "password": "Password123!",
                "role_id": 1,
            },
        )
        login_resp = client.post(
            "/auth/login",
            json={"email": "qe_test_eval@example.com", "password": "Password123!"},
        )

    assert login_resp.status_code == 200, f"QE login failed: {login_resp.text}"
    token = login_resp.json().get("access_token") or login_resp.json().get("access token")
    headers = {"Authorization": f"Bearer {token}"}

    # Test Cases A-E
    test_cases = [
        {
            "label": "A. Cable good image (User Reported Image)",
            "category": "cable",
            "defect_type": "cut",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "cable" / "train" / "good" / "004.png",
            "expected_decision": "Accept",
        },
        {
            "label": "B. Cable defective image",
            "category": "cable",
            "defect_type": "cut_inner_insulation",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "cable" / "test" / "cut_inner_insulation" / "000.png",
            "expected_decision": "Reject",
        },
        {
            "label": "C. Hazelnut defective image",
            "category": "hazelnut",
            "defect_type": "crack",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "hazelnut" / "test" / "crack" / "000.png",
            "expected_decision": "Reject",
        },
        {
            "label": "D. Another MVTec good image (Bottle good)",
            "category": "bottle",
            "defect_type": "good",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "bottle" / "train" / "good" / "000.png",
            "expected_decision": "Accept",
        },
        {
            "label": "E. Another defective image (Bottle defective)",
            "category": "bottle",
            "defect_type": "broken_large",
            "path": PROJECT_ROOT / "mvtec_anomaly_detection" / "bottle" / "test" / "broken_large" / "000.png",
            "expected_decision": "Reject",
        },
    ]

    results = []

    for tc in test_cases:
        print(f"Testing: {tc['label']}")
        img_path = tc["path"]
        assert img_path.exists(), f"Image not found: {img_path}"

        # Upload image
        with open(img_path, "rb") as f:
            file_bytes = f.read()

        upload_resp = client.post(
            "/images/upload",
            headers=headers,
            files={"file": (img_path.name, file_bytes, "image/png")},
        )
        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        image_id = upload_resp.json()["id"]

        # Run AI inspection
        inspect_resp = client.post(
            f"/images/{image_id}/inspect",
            headers=headers,
            json={"category": tc["category"], "defect_type": tc["defect_type"]},
        )
        assert inspect_resp.status_code == 200, f"Inspect failed: {inspect_resp.text}"
        data = inspect_resp.json()

        # Print required fields
        print(f"category               : {data['category']}")
        print(f"defect_type            : {data['defect_type']}")
        print(f"anomaly_score          : {float(data['anomaly_score']):.4f}")
        print(f"confidence_score       : {float(data['confidence_score']):.2f}%")
        print(f"predicted_area_percent : {float(data['predicted_area_percent']):.2f}%")
        print(f"size_score             : {float(data['size_score']):.2f}")
        print(f"location_score         : {float(data['location_score']):.2f}")
        print(f"defect_type_score      : {float(data['defect_type_score']):.2f}")
        print(f"severity_score         : {float(data['severity_score']):.2f}")
        print(f"severity_level         : {data['severity_level']}")
        print(f"quality_decision       : {data['quality_decision']}")

        # Verify overlay endpoint
        overlay_resp = client.get(
            f"/images/{image_id}/inspection-overlay",
            headers=headers,
        )
        assert overlay_resp.status_code == 200, f"Overlay failed: {overlay_resp.status_code}"
        overlay_bytes = overlay_resp.content
        nparr = np.frombuffer(overlay_bytes, np.uint8)
        overlay_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        assert overlay_img is not None, "Failed to decode overlay image"

        orig_img = cv2.imread(str(img_path))
        diff = np.abs(overlay_img.astype(int) - orig_img.astype(int))

        if tc["expected_decision"] == "Accept":
            # Normal image: overlay should be identical to original image (no red pixels)
            assert diff.max() == 0, f"Normal overlay contains false defect marks! Max diff: {diff.max()}"
            print("inspection_overlay     : Verified CLEAN (0 false defect pixels)")
        else:
            # Defective image: overlay should contain red highlights
            has_highlight = (diff > 0).any()
            assert has_highlight, "Defective overlay missing expected defect highlights!"
            print(f"inspection_overlay     : Verified HIGHLIGHTED (defect contour present)")

        assert data["quality_decision"] == tc["expected_decision"], (
            f"Expected {tc['expected_decision']} but got {data['quality_decision']}"
        )

        results.append(data)

    print("Endpoint evaluation: 5/5 passed.")


if __name__ == "__main__":
    run_endpoint_tests()
