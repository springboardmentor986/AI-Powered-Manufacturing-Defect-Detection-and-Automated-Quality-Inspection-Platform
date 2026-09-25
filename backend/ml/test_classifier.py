from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image



PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# 2. MODEL PATH
# ============================================================

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "defect_classifier_resnet18_final.pth"
)

print("Model path:")
print(MODEL_PATH)

print("Model exists:", MODEL_PATH.exists())


# ============================================================
# 3. DEFECT CLASS NAMES
# ============================================================

class_names = [
    "bent",
    "bent_lead",
    "bent_wire",
    "broken",
    "broken_large",
    "broken_small",
    "broken_teeth",
    "cable_swap",
    "color",
    "combined",
    "contamination",
    "crack",
    "cut",
    "cut_inner_insulation",
    "cut_lead",
    "cut_outer_insulation",
    "damaged_case",
    "defective",
    "fabric_border",
    "fabric_interior",
    "faulty_imprint",
    "flip",
    "fold",
    "glue",
    "glue_strip",
    "gray_stroke",
    "hole",
    "liquid",
    "manipulated_front",
    "metal_contamination",
    "misplaced",
    "missing_cable",
    "missing_wire",
    "oil",
    "pill_type",
    "poke",
    "poke_insulation",
    "print",
    "rough",
    "scratch",
    "scratch_head",
    "scratch_neck",
    "split_teeth",
    "squeeze",
    "squeezed_teeth",
    "thread",
    "thread_side",
    "thread_top"
]


# ============================================================
# 4. CHECK CLASS COUNT
# ============================================================

print()
print("Number of classes:", len(class_names))

if len(class_names) != 48:
    raise ValueError(
        f"Expected 48 classes, but found {len(class_names)}"
    )


# ============================================================
# 5. SELECT DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Device:", device)


# ============================================================
# 6. CREATE RESNET18 MODEL
# ============================================================

print()
print("Creating ResNet18...")

model = models.resnet18(weights=None)

# Replace final layer with our 48-class classifier
model.fc = nn.Linear(
    model.fc.in_features,
    48
)


# ============================================================
# 7. LOAD TRAINED WEIGHTS
# ============================================================

print("Loading ResNet18 model...")

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device
)




if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:

    model.load_state_dict(
        checkpoint["model_state_dict"]
    )

else:

    model.load_state_dict(
        checkpoint
    )


model = model.to(device)


model.eval()

print("ResNet18 loaded successfully!")


# ============================================================
# 8. IMAGE PREPROCESSING
# ============================================================

transform = transforms.Compose([

   
    transforms.Resize((224, 224)),

    
    transforms.ToTensor(),

    
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# 9. FIND MVTec TEST IMAGES
# ============================================================

DATASET_PATH = PROJECT_ROOT / "dataset1"

print()
print("Searching for test images in:")
print(DATASET_PATH)



if not DATASET_PATH.exists():

    raise FileNotFoundError(
        f"Dataset folder does not exist:\n{DATASET_PATH}"
    )



image_files = []

for extension in ["*.png", "*.jpg", "*.jpeg", "*.bmp"]:

    image_files.extend(
        DATASET_PATH.glob(
            f"**/test/**/{extension}"
        )
    )



image_files = sorted(
    set(image_files)
)


# ============================================================
# 10. CHECK WHETHER TEST IMAGES EXIST
# ============================================================

if not image_files:

    raise FileNotFoundError(
        f"No test images found inside:\n{DATASET_PATH}\n\n"
        "Check that your MVTec dataset contains test images."
    )


print()
print("Test images found:", len(image_files))


# ============================================================
# 11. SELECT FIRST TEST IMAGE
# ============================================================

image_path = image_files[0]

print()
print("Testing image:")
print(image_path)


# ============================================================
# 12. LOAD IMAGE
# ============================================================

try:

    image = Image.open(
        image_path
    ).convert("RGB")

except Exception as e:

    raise RuntimeError(
        f"Could not load image:\n{image_path}\n\n"
        f"Error: {e}"
    )


print()
print("Image loaded successfully!")

print(
    "Original image size:",
    image.size
)


# ============================================================
# 13. PREPROCESS IMAGE
# ============================================================

image_tensor = transform(image)




image_tensor = image_tensor.unsqueeze(0)



image_tensor = image_tensor.to(device)


# ============================================================
# 14. RUN RESNET18 PREDICTION
# ============================================================

print()
print("Running prediction...")

with torch.no_grad():

    # Raw neural-network output
    output = model(image_tensor)

    # Convert logits to probabilities
    probabilities = torch.softmax(
        output,
        dim=1
    )

    # Get highest probability
    confidence, predicted = torch.max(
        probabilities,
        dim=1
    )


# ============================================================
# 15. GET PREDICTION
# ============================================================

predicted_index = predicted.item()

predicted_class = class_names[
    predicted_index
]

confidence_percentage = (
    confidence.item() * 100
)


# ============================================================
# 16. GET ACTUAL FOLDER NAME
# ============================================================

actual_class = image_path.parent.name


# ============================================================
# 17. DISPLAY RESULT
# ============================================================

print()
print("=" * 55)
print("          RESNET18 CLASSIFICATION RESULT")
print("=" * 55)

print(
    "Image          :",
    image_path.name
)

print(
    "Actual folder  :",
    actual_class
)

print(
    "Predicted      :",
    predicted_class
)

print(
    "Confidence     :",
    round(confidence_percentage, 2),
    "%"
)

print("=" * 55)


# ============================================================
# 18. CONFIDENCE CHECK
# ============================================================

if confidence_percentage < 70:

    print()
    print("MANUAL REVIEW REQUIRED")

    print(
        "Reason: Classification confidence is below 70%."
    )

else:

    print()
    print("Confidence acceptable.")


# ============================================================
# 19. SHOW TOP 5 PREDICTIONS
# ============================================================

top5_probabilities, top5_indices = torch.topk(
    probabilities,
    k=5,
    dim=1
)

print()
print("Top 5 predictions:")
print("-" * 40)

for i in range(5):

    class_index = top5_indices[0][i].item()

    class_probability = (
        top5_probabilities[0][i].item() * 100
    )

    print(
        f"{i + 1}. "
        f"{class_names[class_index]:25s} "
        f"{class_probability:.2f}%"
    )

print("-" * 40)