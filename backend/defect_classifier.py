import joblib
import numpy as np


CLASSIFIER_PATH = "backend/defect_classifier.pkl"


def load_defect_classifier():
    return joblib.load(CLASSIFIER_PATH)


def predict_defect(features):
    classifier = load_defect_classifier()

    features = np.asarray(features)

    if features.ndim == 1:
        features = features.reshape(1, -1)

    prediction = classifier.predict(features)[0]

    return prediction