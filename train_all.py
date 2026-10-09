import os
import subprocess
import sys

# Already trained (skip these):
#   bottle ✅, cable ✅, capsule ✅, carpet ✅, grid ✅
# Training: hazelnut + next 3 (leather, metal_nut, pill)
categories = [
    "hazelnut", "leather", "metal_nut", "pill"
]

python_exe = os.path.join("venv", "Scripts", "python.exe")
failed = []

for cat in categories:
    print(f"==========================================", flush=True)
    print(f"Training category: {cat}", flush=True)
    print(f"==========================================", flush=True)

    cmd = [python_exe, "ml/train_category.py", "--category", cat, "--calibrate"]

    process = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
    )

    process.wait()

    if process.returncode != 0:
        print(f"[ERROR] Training failed for {cat} with exit code {process.returncode}", flush=True)
        failed.append(cat)
    else:
        print(f"[OK] Successfully trained {cat}", flush=True)

print("\n==========================================", flush=True)
print("ALL TRAINING COMPLETE", flush=True)
print("==========================================", flush=True)
if failed:
    print(f"Failed categories: {failed}", flush=True)
else:
    print("All 10 categories trained successfully!", flush=True)

