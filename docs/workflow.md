# VisionInspect AI - Quality Inspection Workflow

## End-to-End Workflow

1. User opens VisionInspect AI.
2. User registers or logs in.
3. Backend validates credentials.
4. JWT token is generated.
5. User role is identified.
6. User is redirected to the appropriate dashboard.
7. Quality Engineer selects New Inspection.
8. Product image is uploaded.
9. Backend validates the image type.
10. Image is stored.
11. Inspection record is created in MongoDB.
12. Inspection status is set to pending.
13. A camera capture can be submitted through the camera integration simulation.
14. Multiple images can be submitted through batch image processing.
15. Each camera or batch image uses the same autoencoder → YOLO inspection pipeline.
16. MVTec AD provides the dataset foundation.
17. Image preprocessing prepares images for ML analysis.

## Role Workflow

Quality Engineer:
Login → Dashboard → Upload Image → Create Inspection

Factory Supervisor:
Login → Dashboard → View Inspection Activity

## Milestone 1 Boundary

Milestone 1 establishes the application foundation,
authentication, image acquisition, inspection workflow,
MVTec AD integration and preprocessing foundation.

Actual AI defect prediction is implemented in later milestones.