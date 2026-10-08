# MVTec AD Dataset Manifest & Analysis

- **Root Directory**: `C:\Users\Dell\Desktop\infosys project\main data`
- **Total Categories**: 15 (5 Texture, 10 Object)
- **Total Images**: 5,354
- **Defect-free Training Images**: 3,629
- **Defect-free Test Images**: 467
- **Defective Test Images**: 1,258

---

## Category-by-Category Breakdown

| Category | Type | Total Images | Train (Good) | Test (Good) | Test (Defects) | Defect Classes |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **bottle** | Object | 292 | 209 | 20 | 63 | `broken_large`, `broken_small`, `contamination` |
| **cable** | Object | 374 | 224 | 58 | 92 | `bent_wire`, `cable_swap`, `combined`, `cut_inner_insulation`, `cut_outer_insulation`, `missing_cable`, `missing_wire`, `poke_insulation` |
| **capsule** | Object | 351 | 219 | 23 | 109 | `crack`, `faulty_imprint`, `poke`, `scratch`, `squeeze` |
| **carpet** | Texture | 397 | 280 | 28 | 89 | `color`, `cut`, `hole`, `metal_contamination`, `thread` |
| **grid** | Texture | 342 | 264 | 21 | 57 | `bent`, `broken`, `glue`, `metal_contamination`, `thread` |
| **hazelnut** | Object | 501 | 391 | 40 | 70 | `crack`, `cut`, `hole`, `print` |
| **leather** | Texture | 369 | 245 | 32 | 92 | `color`, `cut`, `fold`, `glue`, `poke` |
| **metal_nut** | Object | 335 | 220 | 22 | 93 | `bent`, `color`, `flip`, `scratch` |
| **pill** | Object | 434 | 267 | 26 | 141 | `color`, `combined`, `contamination`, `crack`, `faulty_imprint`, `pill_type`, `scratch` |
| **screw** | Object | 480 | 320 | 41 | 119 | `manipulated_front`, `scratch_head`, `scratch_neck`, `thread_side`, `thread_top` |
| **tile** | Texture | 347 | 230 | 33 | 84 | `crack`, `glue_strip`, `gray_stroke`, `oil`, `rough` |
| **toothbrush**| Object | 102 | 60 | 12 | 30 | `defective` |
| **transistor** | Object | 313 | 213 | 60 | 40 | `bent_lead`, `cut_lead`, `damaged_case`, `misplaced` |
| **wood** | Texture | 326 | 247 | 19 | 60 | `color`, `combined`, `hole`, `liquid`, `scratch` |
| **zipper** | Object | 391 | 240 | 32 | 119 | `broken_teeth`, `combined`, `fabric_border`, `fabric_interior`, `rough`, `split_teeth`, `squeezed_teeth` |

---

## Directory Organization Standard
Each category adheres to the strict canonical MVTec AD format:
```text
main data/<category>/
├── train/
│   └── good/              # High-resolution nominal defect-free images
├── test/
│   ├── good/              # Nominal test validation images
│   └── <defect_type>/     # Specific manufacturing defect examples
└── ground_truth/
    └── <defect_type>/     # Binary pixel-level segmentation mask (_mask.png)
```
