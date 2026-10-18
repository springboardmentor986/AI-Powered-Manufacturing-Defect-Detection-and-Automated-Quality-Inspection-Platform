# MVTec AD Industrial Dataset Manifest & Integration

### 1. Dataset Overview
- **Location**: `C:\Users\satya\.gemini\antigravity-ide\scratch\AI-Powered-Manufacturing-Defect-Detection-and-Automated-Quality-Inspection-Platform\mv-dataset` (Active Primary)
- **Total Categories**: 15 Industrial Categories (5 Texture, 10 Object)
- **Total Dataset Images**: 6,612 real high-resolution industrial samples & ground-truth binary masks
- **Trained AI Models**: 15 / 15 Category Models Trained on actual `train/good` dataset (stored in `backend/data/models/*.npz`)
- **Format**: PNG, Ground-truth binary segmentation masks, Train/Test split structure

---

### 2. Category Breakdown & Defect Types

| # | Category | Type | Total Images | Train (Good) | Test (Good) | Test (Defect) | Known Defect Classes |
|---|:---|:---:|:---:|:---:|:---:|:---:|:---|
| 1 | **Bottle** | Object | 292 | 209 | 20 | 63 | `broken_large`, `broken_small`, `contamination` |
| 2 | **Cable** | Object | 374 | 224 | 58 | 92 | `bent_wire`, `cable_swap`, `combined`, `cut_inner_insulation`, `cut_outer_insulation`, `missing_cable`, `missing_wire`, `poke_insulation` |
| 3 | **Capsule** | Object | 351 | 219 | 23 | 109 | `crack`, `faulty_imprint`, `poke`, `scratch`, `squeeze` |
| 4 | **Carpet** | Texture | 391 | 280 | 28 | 83 | `color`, `cut`, `hole`, `metal_contamination`, `thread` |
| 5 | **Grid** | Texture | 341 | 264 | 21 | 56 | `bent`, `broken`, `glue`, `metal_contamination`, `thread` |
| 6 | **Hazelnut** | Object | 501 | 391 | 40 | 70 | `crack`, `cut`, `hole`, `print` |
| 7 | **Leather** | Texture | 357 | 245 | 32 | 80 | `color`, `cut`, `fold`, `glue`, `poke` |
| 8 | **Metal Nut** | Object | 335 | 220 | 22 | 93 | `bent`, `color`, `flip`, `scratch` |
| 9 | **Pill** | Object | 434 | 267 | 26 | 141 | `color`, `combined`, `contamination`, `crack`, `faulty_imprint`, `pill_type`, `scratch` |
| 10 | **Screw** | Object | 480 | 320 | 41 | 119 | `manipulated_front`, `scratch_head`, `scratch_neck`, `thread_side`, `thread_top` |
| 11 | **Tile** | Texture | 345 | 230 | 33 | 82 | `crack`, `glue_strip`, `gray_stroke`, `oil`, `rough` |
| 12 | **Toothbrush**| Object | 102 | 60 | 12 | 30 | `defective` |
| 13 | **Transistor**| Object | 313 | 213 | 60 | 40 | `bent_lead`, `cut_lead`, `damaged_case`, `misplaced` |
| 14 | **Wood** | Texture | 306 | 247 | 19 | 40 | `color`, `hole`, `liquid`, `scratch` |
| 15 | **Zipper** | Object | 462 | 240 | 32 | 190 | `broken_teeth`, `combined`, `fabric_border`, `fabric_interior`, `rough`, `split_teeth`, `squeezed_teeth` |

---

### 3. Pipeline Integration
The dataset is dynamically accessible via the `DatasetService` class in `backend/app/services/dataset_service.py` and visualized through the **MVTec AD Dataset Explorer** component in the React frontend.
