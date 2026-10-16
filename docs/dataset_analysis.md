# MVTec AD Dataset Analysis

## 1. Dataset Overview

The project uses the MVTec Anomaly Detection (MVTec AD) dataset.

The dataset contains 15 object and texture categories. The project will use all 15 categories as instructed.

## 2. Categories

The 15 categories are:

1. bottle
2. cable
3. capsule
4. carpet
5. grid
6. hazelnut
7. leather
8. metal_nut
9. pill
10. screw
11. tile
12. toothbrush
13. transistor
14. wood
15. zipper

## 3. Dataset Distribution

The local dataset inspection produced the following results:

| Category | Train | Test | Good Test | Defective Test |
|---|---:|---:|---:|---:|
| bottle | 209 | 83 | 20 | 63 |
| cable | 224 | 150 | 58 | 92 |
| capsule | 219 | 132 | 23 | 109 |
| carpet | 280 | 117 | 28 | 89 |
| grid | 264 | 78 | 21 | 57 |
| hazelnut | 391 | 110 | 40 | 70 |
| leather | 245 | 124 | 32 | 92 |
| metal_nut | 220 | 115 | 22 | 93 |
| pill | 267 | 167 | 26 | 141 |
| screw | 320 | 160 | 41 | 119 |
| tile | 230 | 117 | 33 | 84 |
| toothbrush | 60 | 42 | 12 | 30 |
| transistor | 213 | 100 | 60 | 40 |
| wood | 247 | 79 | 19 | 60 |
| zipper | 240 | 151 | 32 | 119 |
| **Total** | **3629** | **1725** | — | — |

## 4. Defect Analysis

Each category contains different types of defects.

Examples include:

- bottle: broken_large, broken_small, contamination
- cable: bent_wire, cable_swap, combined, cut_inner_insulation, cut_outer_insulation, missing_cable, missing_wire, poke_insulation
- capsule: crack, faulty_imprint, poke, scratch, squeeze
- screw: manipulated_front, scratch_head, scratch_neck, thread_side, thread_top
- zipper: broken_teeth, combined, fabric_border, fabric_interior, rough, split_teeth, squeezed_teeth

The defect types are category-specific.

## 5. Image Properties

The dataset images were inspected using Python and Pillow.

Findings:

- Image format: PNG
- Images are not all the same resolution.
- Examples of resolutions found include 900×900, 800×800, 700×700, and 1024×1024.
- Most inspected images were RGB.
- Some categories contain grayscale images (`L` mode), including grid, screw, and zipper.

## 6. Data Quality Check

All PNG images in the dataset were checked for readability.

Result:

- Total PNG images checked: 6612
- Corrupted images found: 0

Therefore, no corrupted images were detected during the inspection.

## 7. Initial Analysis Decision

All 15 categories will be retained because the project requirement is to work with all categories.

The different image resolutions and image modes will be handled during preprocessing before model training.

The original dataset files will not be modified.