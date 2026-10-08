import urllib.request
import json
import urllib.parse

def test_api():
    print("[*] Running Milestone 1 Automated System Verification Tests...")

    # 1. Health check
    res = urllib.request.urlopen("http://127.0.0.1:8000/health")
    data = json.loads(res.read().decode())
    assert data["status"] == "healthy", "Health check failed"
    print("  [+] [1/8] Backend health endpoint: OK")

    # 2. Login test
    login_payload = json.dumps({"username": "engineer@visioninspect.ai", "password": "password123"}).encode()
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    auth_data = json.loads(res.read().decode())
    token = auth_data["access_token"]
    assert auth_data["user"]["role"] == "quality_engineer"
    print(f"  [+] [2/8] Quality Engineer login & JWT issuance: OK (Token len: {len(token)})")

    # 3. Role switch test
    req = urllib.request.Request("http://127.0.0.1:8000/api/v1/auth/switch-demo-role?role=factory_supervisor", data=b"")
    res = urllib.request.urlopen(req)
    sup_data = json.loads(res.read().decode())
    assert sup_data["user"]["role"] == "factory_supervisor"
    print("  [+] [3/8] RBAC Role Switching (Factory Supervisor): OK")

    # 4. Dashboard KPIs test
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/dashboard/stats")
    stats = json.loads(res.read().decode())
    assert stats["total_inspections"] > 0
    assert stats["categories_covered"] == 15
    print(f"  [+] [4/8] Dashboard KPIs: {stats['total_inspections']} inspections, {stats['pass_rate_percentage']}% pass rate, {stats['categories_covered']}/15 categories: OK")

    # 5. MVTec AD Categories test
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/dataset/categories")
    cats = json.loads(res.read().decode())
    assert len(cats) == 15, f"Expected 15 categories, got {len(cats)}"
    print("  [+] [5/8] MVTec AD Dataset Explorer (All 15 standard categories verified): OK")

    # 6. MVTec AD Import to live inspection queue
    import_data = urllib.parse.urlencode({
        "category": "tile",
        "split": "test",
        "defect_type": "oil",
        "image_name": "000.png"
    }).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/inspections/import-mvtec",
        data=import_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(req)
    imported = json.loads(res.read().decode())
    assert imported["category"] == "tile"
    print(f"  [+] [6/8] Direct MVTec AD Ingestion to Live Inspection: OK (ID #{imported['id'][:8]}, Decision: {imported['quality_decision']})")

    # 7. Inspection listing & filters
    res = urllib.request.urlopen("http://127.0.0.1:8000/api/v1/inspections?category=tile")
    tile_records = json.loads(res.read().decode())
    assert len(tile_records) >= 1
    print(f"  [+] [7/8] Inspection Records Filtering: OK (Found {len(tile_records)} records for category 'tile')")

    # 8. Frontend Dev Server test
    res = urllib.request.urlopen("http://localhost:5173")
    html_content = res.read().decode()
    assert "VisionInspect" in html_content or "root" in html_content
    print("  [+] [8/8] Vite React Frontend Dev Server: OK (HTTP 200 OK)")

    print("\n[SUCCESS] ALL 8 MILESTONE 1 VERIFICATION TESTS PASSED!")

if __name__ == "__main__":
    test_api()
