"""Train and persist the VisionInspect feature model."""

import json

from defect_model import train_model


if __name__ == "__main__":
    model = train_model()
    print(json.dumps({
        "model": "bottle-only hierarchical random forest feature model",
        "version": model["version"],
        "feature_count": model["feature_count"],
        "samples": sum(model["sample_counts"].values()),
        "sample_counts": model["sample_counts"],
    }, indent=2))
