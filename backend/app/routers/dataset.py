from fastapi import APIRouter, HTTPException
import os

router = APIRouter(prefix="/dataset", tags=["Dataset"])

MVTEC_CATEGORIES = [
    "bottle", "cable", "capsule", "carpet", "grid",
    "hazelnut", "leather", "metal_nut", "pill", "screw",
    "tile", "toothbrush", "transistor", "wood", "zipper"
]

@router.get("/categories")
def get_categories():
    return {"categories": MVTEC_CATEGORIES}

@router.get("/category/{category_name}")
def get_category_images(category_name: str):
    if category_name not in MVTEC_CATEGORIES:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Try all possible paths
    paths = [
        f"dataset/{category_name}/test/good",
        f"dataset/{category_name}/good",
        f"dataset/{category_name}/test",
        f"dataset/{category_name}",
    ]
    
    found_path = None
    for path in paths:
        if os.path.exists(path):
            # Check if there are images
            files = [f for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if files:
                found_path = path
                break
    
    if not found_path:
        return {
            "category": category_name,
            "image_count": 0,
            "images": [],
            "available": False
        }
    
    # Get all images
    images = []
    for file in os.listdir(found_path):
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            images.append(file)
    
    images = sorted(images)
    
    return {
        "category": category_name,
        "image_count": len(images),
        "images": images,
        "available": len(images) > 0,
        "path": found_path
    }

@router.get("/image/{category}/{filename}")
def get_image(category: str, filename: str):
    from fastapi.responses import FileResponse
    
    paths = [
        f"dataset/{category}/test/good/{filename}",
        f"dataset/{category}/good/{filename}",
        f"dataset/{category}/test/{filename}",
        f"dataset/{category}/{filename}",
    ]
    
    for path in paths:
        if os.path.exists(path):
            return FileResponse(path)
    
    raise HTTPException(status_code=404, detail="Image not found")
