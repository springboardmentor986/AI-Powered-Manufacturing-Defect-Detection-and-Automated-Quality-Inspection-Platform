import os
import shutil
import uuid

import cv2
import joblib
import numpy as np

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware

from skimage.feature import (
    hog,
    local_binary_pattern
)

from backend.database import (
    init_db,
    get_db_connection
)

from backend.image_quality import (
    analyze_image_quality
)

from backend.severity import (
    calculate_severity
)

from backend.risk_assessment import (
    calculate_risk
)

# ============================================================
# MILESTONE 3 ANALYTICS
# Read-only analytics module
# ============================================================

from backend.analytics import get_analytics


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "uploads"
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "processed"
)

ANOMALY_MODEL_PATH = os.path.join(
    BASE_DIR,
    "backend",
    "anomaly_model.pkl"
)

DEFECT_MODEL_PATH = os.path.join(
    BASE_DIR,
    "backend",
    "defect_model.pkl"
)


# ============================================================
# DIRECTORIES
# ============================================================

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

os.makedirs(
    PROCESSED_DIR,
    exist_ok=True
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="VisionInspect AI",
    description=(
        "AI-Powered Manufacturing Defect "
        "Detection and Automated Quality "
        "Inspection Platform"
    ),
    version="4.1"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# LOAD ANOMALY MODEL
# ============================================================

anomaly_model = None

try:

    if os.path.exists(
        ANOMALY_MODEL_PATH
    ):

        anomaly_model = joblib.load(
            ANOMALY_MODEL_PATH
        )

        print(
            "✓ Anomaly model loaded"
        )

    else:

        print(
            "⚠ anomaly_model.pkl not found"
        )

except Exception as e:

    print(
        f"✗ Anomaly model error: {e}"
    )


# ============================================================
# LOAD DEFECT MODEL
# ============================================================

defect_model = None

try:

    if os.path.exists(
        DEFECT_MODEL_PATH
    ):

        defect_model = joblib.load(
            DEFECT_MODEL_PATH
        )

        print(
            "✓ ML defect model loaded"
        )

    else:

        print(
            "⚠ defect_model.pkl not found"
        )

except Exception as e:

    print(
        f"✗ Defect model error: {e}"
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "project": "VisionInspect AI",
        "version": "4.1",
        "status": "running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "healthy",

        "anomaly_model":
            "loaded"
            if anomaly_model is not None
            else "not loaded",

        "defect_model":
            "loaded"
            if defect_model is not None
            else "not loaded",

        "database":
            "connected"
    }


# ============================================================
# IMAGE VALIDATION
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


def validate_image(filename):

    if not filename:

        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported image format. "
                "Use JPG, JPEG, PNG, BMP or WEBP."
            )
        )


# ============================================================
# ANOMALY FEATURES
# ============================================================

def extract_anomaly_features(image):

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(
        gray,
        (128, 128)
    )

    features = hog(
        gray,
        orientations=9,
        pixels_per_cell=(16, 16),
        cells_per_block=(2, 2),
        block_norm="L2-Hys"
    )

    return features.reshape(
        1,
        -1
    )


# ============================================================
# DEFECT MODEL FEATURES
# ============================================================

def extract_defect_features(image):

    image = cv2.resize(
        image,
        (128, 128)
    )

    image = cv2.GaussianBlur(
        image,
        (3, 3),
        0
    )

    # --------------------------------------------------------
    # HOG
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    hog_features = hog(
        gray,
        orientations=9,
        pixels_per_cell=(8, 8),
        cells_per_block=(2, 2),
        block_norm="L2-Hys"
    )

    # --------------------------------------------------------
    # HSV
    # --------------------------------------------------------

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV
    )

    h_hist = cv2.calcHist(
        [hsv],
        [0],
        None,
        [32],
        [0, 180]
    ).flatten()

    s_hist = cv2.calcHist(
        [hsv],
        [1],
        None,
        [32],
        [0, 256]
    ).flatten()

    v_hist = cv2.calcHist(
        [hsv],
        [2],
        None,
        [32],
        [0, 256]
    ).flatten()

    h_hist = h_hist / (
        np.sum(h_hist) + 1e-8
    )

    s_hist = s_hist / (
        np.sum(s_hist) + 1e-8
    )

    v_hist = v_hist / (
        np.sum(v_hist) + 1e-8
    )

    color_features = np.concatenate([
        h_hist,
        s_hist,
        v_hist
    ])

    # --------------------------------------------------------
    # LBP
    # --------------------------------------------------------

    lbp = local_binary_pattern(
        gray,
        P=16,
        R=2,
        method="uniform"
    )

    lbp_hist, _ = np.histogram(
        lbp.ravel(),
        bins=np.arange(0, 19),
        range=(0, 18)
    )

    lbp_hist = lbp_hist.astype(
        np.float32
    )

    lbp_hist = lbp_hist / (
        np.sum(lbp_hist) + 1e-8
    )

    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    features = np.concatenate([
        hog_features,
        color_features,
        lbp_hist
    ])

    return features.reshape(
        1,
        -1
    ).astype(
        np.float32
    )


# ============================================================
# ML DEFECT CLASSIFICATION
# ============================================================

def classify_uploaded_image(image):

    """
    Classifies a new uploaded image using
    the trained ML defect model.
    """

    if defect_model is None:

        return {
            "defect_type": "Unknown",
            "defect_category": "unknown",
            "confidence": None
        }

    try:

        features = extract_defect_features(
            image
        )

        # ----------------------------------------------------
        # PREDICTION
        # ----------------------------------------------------

        prediction = defect_model.predict(
            features
        )[0]

        # ----------------------------------------------------
        # PROBABILITY
        # ----------------------------------------------------

        probabilities = (
            defect_model.predict_proba(
                features
            )[0]
        )

        # Existing trained model is expected
        # to be a Pipeline with a classifier step.
        classifier = (
            defect_model.named_steps[
                "classifier"
            ]
        )

        classes = classifier.classes_

        best_index = int(
            np.argmax(probabilities)
        )

        confidence = float(
            probabilities[best_index]
        ) * 100

        prediction = str(
            prediction
        )

        # ----------------------------------------------------
        # MAP RESULT
        # ----------------------------------------------------

        if prediction == "good":

            return {
                "defect_type":
                    "No Defect",

                "defect_category":
                    "good",

                "confidence":
                    round(
                        confidence,
                        2
                    )
            }

        elif prediction == "broken_large":

            return {
                "defect_type":
                    "Broken Large",

                "defect_category":
                    "structural",

                "confidence":
                    round(
                        confidence,
                        2
                    )
            }

        elif prediction == "broken_small":

            return {
                "defect_type":
                    "Broken Small",

                "defect_category":
                    "structural",

                "confidence":
                    round(
                        confidence,
                        2
                    )
            }

        elif prediction == "contamination":

            return {
                "defect_type":
                    "Contamination",

                "defect_category":
                    "surface",

                "confidence":
                    round(
                        confidence,
                        2
                    )
            }

        return {
            "defect_type":
                "Unknown",

            "defect_category":
                "unknown",

            "confidence":
                round(
                    confidence,
                    2
                )
        }

    except Exception as e:

        print(
            "\n=========================================="
        )

        print(
            "DEFECT CLASSIFICATION ERROR"
        )

        print(
            "=========================================="
        )

        print(
            str(e)
        )

        print(
            "==========================================\n"
        )

        return {
            "defect_type":
                "Unknown",

            "defect_category":
                "unknown",

            "confidence":
                None
        }


# ============================================================
# UPLOAD
# ============================================================

@app.post("/upload")
async def upload_image(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validate_image(
        file.filename
    )

    # --------------------------------------------------------
    # UNIQUE FILE
    # --------------------------------------------------------

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    unique_filename = (
        uuid.uuid4().hex +
        extension
    )

    upload_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    processed_filename = (
        "processed_" +
        unique_filename
    )

    processed_path = os.path.join(
        PROCESSED_DIR,
        processed_filename
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    try:

        with open(
            upload_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save image: {e}"
        )

    # --------------------------------------------------------
    # READ IMAGE
    # --------------------------------------------------------

    image = cv2.imread(
        upload_path
    )

    if image is None:

        raise HTTPException(
            status_code=400,
            detail="Invalid image file."
        )

    # ========================================================
    # IMAGE QUALITY
    # ========================================================

    try:

        quality_result = (
            analyze_image_quality(
                upload_path
            )
        )

        quality_score = float(
            quality_result.get(
                "quality_score",
                0
            )
        )

    except Exception as e:

        print(
            f"Image quality error: {e}"
        )

        quality_result = {
            "quality_score": 0
        }

        quality_score = 0

    # ========================================================
    # IMAGE PREPROCESSING
    # ========================================================

    processed_image = cv2.resize(
        image,
        (512, 512)
    )

    processed_image = cv2.GaussianBlur(
        processed_image,
        (3, 3),
        0
    )

    cv2.imwrite(
        processed_path,
        processed_image
    )

    # ========================================================
    # ANOMALY DETECTION
    # ========================================================

    anomaly_score = 0.0

    anomaly_prediction = "NORMAL"

    if anomaly_model is not None:

        try:

            features = (
                extract_anomaly_features(
                    image
                )
            )

            prediction = anomaly_model.predict(
                features
            )[0]

            anomaly_score = float(
                anomaly_model.decision_function(
                    features
                )[0]
            )

            if prediction == -1:

                anomaly_prediction = (
                    "DEFECTIVE"
                )

            else:

                anomaly_prediction = (
                    "NORMAL"
                )

        except Exception as e:

            print(
                f"Anomaly detection error: {e}"
            )

    # ========================================================
    # ML DEFECT CLASSIFICATION
    # ========================================================

    defect_result = classify_uploaded_image(
        image
    )

    defect_type = defect_result[
        "defect_type"
    ]

    defect_category = defect_result[
        "defect_category"
    ]

    classifier_confidence = (
        defect_result[
            "confidence"
        ]
    )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    ai_prediction = "NORMAL"

    # --------------------------------------------------------
    # HIGH-CONFIDENCE GOOD
    # --------------------------------------------------------

    if defect_category == "good":

        if (
            classifier_confidence is not None
            and classifier_confidence >= 60
        ):

            ai_prediction = "NORMAL"

        else:

            ai_prediction = (
                anomaly_prediction
            )

    # --------------------------------------------------------
    # DEFECT CLASS
    # --------------------------------------------------------

    elif defect_category in {
        "structural",
        "surface"
    }:

        if (
            classifier_confidence is not None
            and classifier_confidence >= 50
        ):

            ai_prediction = "DEFECTIVE"

        else:

            ai_prediction = (
                anomaly_prediction
            )

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    else:

        ai_prediction = (
            anomaly_prediction
        )

    # --------------------------------------------------------
    # STRONG DEFECT OVERRIDE
    # --------------------------------------------------------

    if (
        defect_category in {
            "structural",
            "surface"
        }
        and classifier_confidence is not None
        and classifier_confidence >= 80
    ):

        ai_prediction = "DEFECTIVE"

    # --------------------------------------------------------
    # STRONG ANOMALY OVERRIDE
    # --------------------------------------------------------

    if (
        anomaly_prediction == "DEFECTIVE"
        and classifier_confidence is not None
        and classifier_confidence < 50
    ):

        ai_prediction = "DEFECTIVE"

    # --------------------------------------------------------
    # NORMAL RESULT
    # --------------------------------------------------------

    if ai_prediction == "NORMAL":

        defect_type = "No Defect"

        defect_category = "good"

    # ========================================================
    # SEVERITY
    # ========================================================

    if (
        ai_prediction == "NORMAL"
        or defect_type == "No Defect"
    ):

        severity_score = 0.0
        severity_level = "Low"

    else:

        try:

            severity_result = calculate_severity(
                anomaly_score,
                quality_score,
                defect_type,
                classifier_confidence
            )

            severity_score = float(
                severity_result.get(
                    "severity_score",
                    0
                )
            )

            severity_level = (
                severity_result.get(
                    "severity_level",
                    "Low"
                )
            )

        except Exception as e:

            print(
                f"Severity calculation error: {e}"
            )

            severity_score = 0.0
            severity_level = "Low"

    # ========================================================
    # RISK ASSESSMENT
    # ========================================================

    if (
        ai_prediction == "NORMAL"
        or defect_type == "No Defect"
    ):

        risk_score = 0.0

        risk_level = "Low"

        risk_recommendation = (
            "Product can proceed with normal quality monitoring."
        )

    else:

        try:

            risk_result = calculate_risk(
                severity_score,
                severity_level,
                defect_type,
                classifier_confidence
            )

            risk_score = float(
                risk_result.get(
                    "risk_score",
                    0
                )
            )

            risk_level = risk_result.get(
                "risk_level",
                "Low"
            )

            risk_recommendation = (
                risk_result.get(
                    "recommendation",
                    "No recommendation available."
                )
            )

        except Exception as e:

            print(
                f"Risk assessment error: {e}"
            )

            risk_score = 0.0

            risk_level = "Low"

            risk_recommendation = (
                "No recommendation available."
            )

    # ========================================================
    # DATABASE
    #
    # IMPORTANT:
    # Existing database schema is preserved.
    # Existing records are NOT modified.
    # ========================================================

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO inspections
            (
                user_id,
                image_name,
                status,
                processed_path,
                anomaly_score,
                quality_score,
                final_decision,
                defect_type,
                defect_category,
                severity_score,
                severity_level,
                risk_score,
                risk_level,
                risk_recommendation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                file.filename,
                ai_prediction,
                processed_path,
                anomaly_score,
                quality_score,
                ai_prediction,
                defect_type,
                defect_category,
                severity_score,
                severity_level,
                risk_score,
                risk_level,
                risk_recommendation
            )
        )

        inspection_id = (
            cursor.lastrowid
        )

        connection.commit()

    except Exception as e:

        if connection:

            connection.rollback()

        print(
            f"Database error: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}"
        )

    finally:

        if connection:

            connection.close()

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        "inspection_id":
            inspection_id,

        "filename":
            file.filename,

        "ai_prediction":
            ai_prediction,

        "anomaly_score":
            round(
                anomaly_score,
                4
            ),

        "defect_type":
            defect_type,

        "defect_category":
            defect_category,

        "classifier_confidence":
            classifier_confidence,

        "severity_score":
            round(
                severity_score,
                2
            ),

        "severity_level":
            severity_level,

        "risk_score":
            round(
                risk_score,
                2
            ),

        "risk_level":
            risk_level,

        "risk_recommendation":
            risk_recommendation,

        "quality_score":
            round(
                quality_score,
                2
            ),

        "quality_analysis":
            quality_result,

        "processed_image":
            processed_filename,

        "decision":
            ai_prediction
    }


# ============================================================
# HISTORY
# ============================================================

@app.get("/history")
def get_history():

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                inspection_id,
                image_name,
                upload_time,
                status,
                anomaly_score,
                quality_score,
                final_decision,
                defect_type,
                defect_category,
                severity_score,
                severity_level,
                risk_score,
                risk_level,
                risk_recommendation,
                processed_path
            FROM inspections
            ORDER BY inspection_id DESC
            """
        )

        rows = cursor.fetchall()

        history = []

        for row in rows:

            history.append({

                "inspection_id":
                    row[0],

                "image_name":
                    row[1],

                "upload_time":
                    row[2],

                "status":
                    row[3],

                "anomaly_score":
                    row[4],

                "quality_score":
                    row[5],

                "final_decision":
                    row[6],

                "defect_type":
                    row[7],

                "defect_category":
                    row[8],

                "severity_score":
                    row[9],

                "severity_level":
                    row[10],

                "risk_score":
                    row[11],

                "risk_level":
                    row[12],

                "risk_recommendation":
                    row[13],

                "processed_path":
                    row[14]
            })

        return history

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"History error: {e}"
        )

    finally:

        if connection:

            connection.close()


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard():

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM inspections
            """
        )

        total = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM inspections
            WHERE status = 'NORMAL'
            """
        )

        normal = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM inspections
            WHERE status = 'DEFECTIVE'
            """
        )

        defective = cursor.fetchone()[0]

        return {

            "total_inspections":
                total,

            "normal":
                normal,

            "defective":
                defective
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Dashboard error: {e}"
        )

    finally:

        if connection:

            connection.close()


# ============================================================
# MILESTONE 3 - MANUFACTURING ANALYTICS
# ============================================================
#
# IMPORTANT:
# This endpoint is READ-ONLY.
#
# It does NOT:
# - insert records
# - update records
# - delete records
# - modify the database schema
#
# It only reads the existing inspections table.
# ============================================================

@app.get("/analytics")
def analytics():

    try:

        return get_analytics()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Analytics error: {e}"
        )


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(
    email: str,
    password: str
):

    connection = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                role
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (
                email,
                password
            )
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        return {

            "success":
                True,

            "user_id":
                user[0],

            "name":
                user[1],

            "email":
                user[2],

            "role":
                user[3]
        }

    finally:

        if connection:

            connection.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )