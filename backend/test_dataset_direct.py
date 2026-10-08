import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.dataset_service import DatasetService

def main():
    print("=== MVTec AD Dataset Verification ===")
    print(f"Detected MVTEC_DIR: {settings.MVTEC_DIR}")
    print(f"Path exists: {settings.MVTEC_DIR.exists()}")
    
    categories = DatasetService.get_available_categories()
    total_images = sum(c["total_images"] for c in categories)
    total_train = sum(c["train_images"] for c in categories)
    total_test_defect = sum(c["test_defect_images"] for c in categories)
    total_test_good = sum(c["test_good_images"] for c in categories)
    
    print(f"\nTotal Categories: {len(categories)}")
    print(f"Total Images: {total_images}")
    print(f"  - Train (Good): {total_train}")
    print(f"  - Test (Good): {total_test_good}")
    print(f"  - Test (Defects): {total_test_defect}")
    print("-" * 60)
    for c in categories:
        print(f"  [{'x' if c['is_loaded'] else ' '}] {c['category']:<12} | Total: {c['total_images']:<5} | Train: {c['train_images']:<4} | Test Defects: {c['test_defect_images']:<4} | Defect Types: {len(c['defect_types'])}")
    print("=" * 60)

if __name__ == "__main__":
    main()
