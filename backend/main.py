from pathlib import Path
import uuid
import csv
import io

from datetime import datetime, timedelta, timezone

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from fastapi.responses import StreamingResponse

from jose import JWTError, jwt

from passlib.context import CryptContext

from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import User, Inspection
from schemas import UserCreate, UserLogin

from ml.ml_service import inspect_uploaded_image

from ml.severity import (
    get_defect_type_score,
    calculate_severity,
    check_confidence,
    assess_quality,
)

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


app = FastAPI(
    title="VisionInspect AI",
    description="AI Manufacturing Quality Inspection API",
    version="1.0.0",
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()




SECRET_KEY = "visioninspect-secret-key"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

security = HTTPBearer()




def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )



def create_access_token(
    user_id: int,
    role: str,
):

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )



def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

        user_id = int(user_id)

    except (
        JWTError,
        ValueError,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    return user



def require_role(required_role: str):

    def role_checker(
        current_user: User = Depends(
            get_current_user
        ),
    ):

        if current_user.role != required_role:

            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

        return current_user

    return role_checker


def require_quality_engineer(
    current_user: User = Depends(
        get_current_user
    ),
):

    if current_user.role != "quality_engineer":

        raise HTTPException(
            status_code=403,
            detail="Quality Engineer access required",
        )

    return current_user


def require_supervisor(
    current_user: User = Depends(
        get_current_user
    ),
):

    if current_user.role != "factory_supervisor":

        raise HTTPException(
            status_code=403,
            detail="Factory Supervisor access required",
        )

    return current_user




@app.get("/")
def root():

    return {
        "message": "VisionInspect AI API is running",
        "version": "1.0.0",
    }




@app.get("/db-test")
def db_test(
    db: Session = Depends(get_db),
):

    try:

        db.query(User).first()

        return {
            "status": "success",
            "message": "Database connection successful",
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )




@app.post("/auth/register")
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):

    existing_user = (
        db.query(User)
        .filter(
            User.email == user_data.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    if user_data.role not in [
        "quality_engineer",
        "factory_supervisor",
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        ),
        role=user_data.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
    }




@app.post("/auth/login")
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(
            User.email == user_data.email
        )
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        user_data.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user.id,
        user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }



@app.get("/auth/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }




@app.get("/users")
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_supervisor
    ),
):

    users = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }
        for user in users
    ]




@app.post("/users")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_supervisor
    ),
):

    existing_user = (
        db.query(User)
        .filter(
            User.email == user_data.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    if user_data.role not in [
        "quality_engineer",
        "factory_supervisor",
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(
            user_data.password
        ),
        role=user_data.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
        },
    }




@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_supervisor
    ),
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    name = user_data.get(
        "name",
        user.name,
    )

    email = user_data.get(
        "email",
        user.email,
    )

    role = user_data.get(
        "role",
        user.role,
    )

    if role not in [
        "quality_engineer",
        "factory_supervisor",
    ]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role",
        )

    email_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.id != user_id,
        )
        .first()
    )

    if email_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    user.name = name
    user.email = email
    user.role = role

    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }




@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_supervisor
    ),
):

    if current_user.id == user_id:

        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    db.delete(user)
    db.commit()

    return {
        "message": "User deleted successfully"
    }




@app.post("/inspection/predict")
async def inspection_predict(
    file: UploadFile = File(...),
    product_category: str = Form(
        default="unknown"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_quality_engineer
    ),
):

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    file_extension = Path(
        file.filename
    ).suffix.lower()

    if file_extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Unsupported image format",
        )

    image_bytes = await file.read()

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Empty image file",
        )

    try:

        result = inspect_uploaded_image(
            image_bytes
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Inspection failed: {str(e)}",
        )

    detections = result.get(
        "detections",
        [],
    )

    if not isinstance(detections, list):
        detections = []

    

    prediction = result.get("status", "REVIEW")

    allowed_statuses = {
        "PASS",
        "FAIL",
        "REWORK",
        "REVIEW",
    }

    if prediction not in allowed_statuses:
        prediction = "REVIEW"

    
    selected_detection = None

    if detections:

        selected_detection = max(
            detections,
            key=lambda x: (
                x.get("severity_score") or 0
            ),
        )

    
    filename = (
        f"{uuid.uuid4().hex}"
        f"{file_extension}"
    )

    upload_directory = (
        Path(__file__).resolve().parent
        / "uploads"
    )

    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_path = (
        upload_directory
        / filename
    )

    image_path.write_bytes(
        image_bytes
    )

    
    defect_type = None
    classification_confidence = None
    severity_score = None
    severity_level = None
    recommended_action = None
    manual_review = False

    if selected_detection:

        defect_type = selected_detection.get(
            "defect_type"
        )

        classification_confidence = (
            selected_detection.get(
                "classification_confidence"
            )
        )

        severity_score = (
            selected_detection.get(
                "severity_score"
            )
        )

        severity_level = (
            selected_detection.get(
                "severity_level"
            )
        )

        recommended_action = (
            selected_detection.get(
                "recommended_action"
            )
        )

        manual_review = (
            selected_detection.get(
                "manual_review",
                False,
            )
        )

    

    inspection = Inspection(
        user_id=current_user.id,
        image_path=str(image_path),
        product_category=product_category,

        prediction=prediction,

        anomaly_score=0.0,
        threshold=0.25,

        defect_type=defect_type,
        classification_confidence=(
            classification_confidence
        ),
        severity_score=severity_score,
        severity_level=severity_level,
        recommended_action=recommended_action,
        manual_review=manual_review,
    )

    db.add(inspection)
    db.commit()
    db.refresh(inspection)

   
    return {
        "message": "Inspection completed successfully",

        "id": inspection.id,

        "filename": file.filename,

        "category": product_category,

        "prediction": prediction,

        "anomaly_score": 0.0,

        "threshold": 0.25,

        "inspected_by": current_user.name,

        "inspected_by_role": current_user.role,

        "defect_count": len(detections),

        "detections": detections,
    }




@app.get("/inspections")
def get_inspections(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    inspections = (
        db.query(Inspection)
        .order_by(
            Inspection.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": inspection.id,
            "user_id": inspection.user_id,
            "image_path": inspection.image_path,
            "product_category": (
                inspection.product_category
            ),
            "prediction": inspection.prediction,
            "anomaly_score": (
                inspection.anomaly_score
            ),
            "threshold": inspection.threshold,
            "defect_type": (
                inspection.defect_type
            ),
            "classification_confidence": (
                inspection.classification_confidence
            ),
            "severity_score": (
                inspection.severity_score
            ),
            "severity_level": (
                inspection.severity_level
            ),
            "recommended_action": (
                inspection.recommended_action
            ),
            "manual_review": (
                inspection.manual_review
            ),
            "created_at": (
                inspection.created_at
            ),
        }
        for inspection in inspections
    ]




@app.post("/defects/classify")
async def classify_defect(
    file: UploadFile = File(...),
    current_user: User = Depends(
        get_current_user
    ),
):

    image_bytes = await file.read()

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="Empty image file",
        )

    try:

        result = inspect_uploaded_image(
            image_bytes
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}",
        )

    detections = result.get(
        "detections",
        [],
    )

    if not isinstance(detections, list):
        detections = []

    status = result.get("status", "REVIEW")

    allowed_statuses = {
        "PASS",
        "FAIL",
        "REWORK",
        "REVIEW",
    }

    if status not in allowed_statuses:
        status = "REVIEW"

    message_map = {
        "PASS": "No actionable defect detected",
        "FAIL": "Critical defect detected",
        "REWORK": "Defect requires rework",
        "REVIEW": "Inspection requires review",
    }

    return {
        "status": status,
        "message": message_map[status],
        "defects_detected": len(detections),
        "detections": detections,
    }




@app.get("/defects/{inspection_id}/severity")
def get_defect_severity(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    inspection = (
        db.query(Inspection)
        .filter(
            Inspection.id == inspection_id
        )
        .first()
    )

    if inspection is None:

        raise HTTPException(
            status_code=404,
            detail="Inspection not found",
        )

    if inspection.defect_type is None:

        return {
            "inspection_id": inspection.id,
            "message": (
                "No defect severity information available"
            ),
            "severity_score": None,
            "severity_level": None,
            "recommended_action": None,
        }

    return {
        "inspection_id": inspection.id,
        "defect_type": inspection.defect_type,
        "classification_confidence": (
            inspection.classification_confidence
        ),
        "severity_score": (
            inspection.severity_score
        ),
        "severity_level": (
            inspection.severity_level
        ),
        "recommended_action": (
            inspection.recommended_action
        ),
        "manual_review": (
            inspection.manual_review
        ),
    }




@app.get(
    "/inspections/{inspection_id}/quality-report"
)
def get_quality_report(
    inspection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    inspection = (
        db.query(Inspection)
        .filter(
            Inspection.id == inspection_id
        )
        .first()
    )

    if inspection is None:

        raise HTTPException(
            status_code=404,
            detail="Inspection not found",
        )

    return {
        "inspection_id": inspection.id,

        "inspection_date": (
            inspection.created_at
        ),

        "product_category": (
            inspection.product_category
        ),

        "prediction": (
            inspection.prediction
        ),

        "quality_assessment": {
            "status": inspection.prediction,
            "manual_review": (
                inspection.manual_review
            ),
        },

        "defect": {
            "type": inspection.defect_type,
            "classification_confidence": (
                inspection.classification_confidence
            ),
        },

        "severity": {
            "score": inspection.severity_score,
            "level": inspection.severity_level,
            "recommended_action": (
                inspection.recommended_action
            ),
        },

        "inspection": {
            "inspected_by": inspection.user_id,
            "anomaly_score": (
                inspection.anomaly_score
            ),
            "threshold": inspection.threshold,
        },
    }



@app.get("/reports/quality-summary")
def quality_summary(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    if days not in [7, 30, 90]:

        raise HTTPException(
            status_code=400,
            detail="Days must be one of: 7, 30, or 90",
        )

    end_date = datetime.now(
        timezone.utc
    )

    start_date = (
        end_date
        - timedelta(days=days)
    )

    inspections = (
        db.query(Inspection)
        .filter(
            Inspection.created_at >= start_date,
            Inspection.created_at <= end_date,
        )
        .order_by(
            Inspection.created_at.asc()
        )
        .all()
    )

    total_inspections = len(
        inspections
    )

    passed = 0
    failed = 0
    rework = 0
    review = 0
    manual_review = 0

    defect_distribution = {}

    severity_distribution = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
    }

    for inspection in inspections:

        action = (
            inspection.recommended_action
        )

        if action == "Reject":
            failed += 1

        elif action == "Rework":
            rework += 1

        elif action == "Review":
            review += 1

        elif (
            inspection.prediction == "PASS"
            or action == "Accept"
        ):
            passed += 1

        if inspection.manual_review:
            manual_review += 1

        if inspection.defect_type:

            defect_distribution[
                inspection.defect_type
            ] = (
                defect_distribution.get(
                    inspection.defect_type,
                    0,
                )
                + 1
            )

        if inspection.severity_level:

            if (
                inspection.severity_level
                in severity_distribution
            ):

                severity_distribution[
                    inspection.severity_level
                ] += 1

    quality_decided = (
        passed
        + failed
        + rework
        + review
    )

    pass_rate = (
        (passed / quality_decided) * 100
        if quality_decided
        else 0
    )

    defect_rate = (
        (
            (
                failed
                + rework
                + review
            )
            / quality_decided
        )
        * 100
        if quality_decided
        else 0
    )

    return {
        "report": "Quality Summary",
        "period": f"Last {days} days",

        "total_inspections": (
            total_inspections
        ),

        "quality_decided_inspections": (
            quality_decided
        ),

        "passed": passed,
        "failed": failed,
        "rework": rework,
        "review": review,
        "manual_review": manual_review,

        "pass_rate": round(
            pass_rate,
            2,
        ),

        "defect_rate": round(
            defect_rate,
            2,
        ),

        "defect_distribution": (
            defect_distribution
        ),

        "severity_distribution": (
            severity_distribution
        ),
    }




@app.get("/reports/quality-summary/pdf")
def export_quality_summary_pdf(
    days: int = 30,
    current_user: User = Depends(get_current_user),
):

    if days not in [7, 30, 90]:

        raise HTTPException(
            status_code=400,
            detail="days must be 7, 30, or 90",
        )

    db: Session = SessionLocal()

    try:

        start_date = (
            datetime.now(timezone.utc)
            - timedelta(days=days)
        )

        inspections = (
            db.query(Inspection)
            .filter(
                Inspection.created_at >= start_date
            )
            .order_by(
                Inspection.created_at.desc()
            )
            .all()
        )

        total_inspections = len(
            inspections
        )

        passed = 0
        failed = 0
        rework = 0
        review = 0
        manual_review = 0

        severity_distribution = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
        }

        defect_distribution = {}

        for inspection in inspections:

            action = inspection.recommended_action

            if action == "Reject":
                failed += 1

            elif action == "Rework":
                rework += 1

            elif action == "Review":
                review += 1

            elif (
                inspection.prediction == "PASS"
                or action == "Accept"
            ):
                passed += 1

            if inspection.manual_review:
                manual_review += 1

            if inspection.severity_level:

                if (
                    inspection.severity_level
                    in severity_distribution
                ):

                    severity_distribution[
                        inspection.severity_level
                    ] += 1

            if inspection.defect_type:

                defect_distribution[
                    inspection.defect_type
                ] = (
                    defect_distribution.get(
                        inspection.defect_type,
                        0,
                    )
                    + 1
                )

        quality_decided = (
            passed
            + failed
            + rework
            + review
        )

        pass_rate = (
            (passed / quality_decided) * 100
            if quality_decided > 0
            else 0
        )

        defect_rate = (
            (
                (failed + rework + review)
                / quality_decided
            )
            * 100
            if quality_decided > 0
            else 0
        )

        

        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]

        elements = []

        elements.append(
            Paragraph(
                "VisionInspect AI - Quality Report",
                title_style,
            )
        )

        elements.append(
            Spacer(1, 10)
        )

        elements.append(
            Paragraph(
                f"Reporting Period: Last {days} days",
                normal_style,
            )
        )

        elements.append(
            Paragraph(
                f"Generated: "
                f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                normal_style,
            )
        )

        elements.append(
            Spacer(1, 20)
        )

        
        elements.append(
            Paragraph(
                "Quality Summary",
                heading_style,
            )
        )

        summary_data = [
            ["Metric", "Value"],
            ["Total Inspections", str(total_inspections)],
            ["Quality Decided", str(quality_decided)],
            ["Passed", str(passed)],
            ["Failed", str(failed)],
            ["Rework", str(rework)],
            ["Review", str(review)],
            ["Manual Review", str(manual_review)],
            ["Pass Rate", f"{pass_rate:.1f}%"],
            ["Defect Rate", f"{defect_rate:.1f}%"],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[250, 150],
        )

        summary_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1e293b"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, -1),
                        colors.whitesmoke,
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        elements.append(
            summary_table
        )

        elements.append(
            Spacer(1, 20)
        )

       
        elements.append(
            Paragraph(
                "Severity Distribution",
                heading_style,
            )
        )

        severity_data = [
            ["Severity Level", "Count"],
            [
                "Critical",
                str(
                    severity_distribution[
                        "Critical"
                    ]
                ),
            ],
            [
                "High",
                str(
                    severity_distribution[
                        "High"
                    ]
                ),
            ],
            [
                "Medium",
                str(
                    severity_distribution[
                        "Medium"
                    ]
                ),
            ],
            [
                "Low",
                str(
                    severity_distribution[
                        "Low"
                    ]
                ),
            ],
        ]

        severity_table = Table(
            severity_data,
            colWidths=[250, 150],
        )

        severity_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1e293b"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        elements.append(
            severity_table
        )

        elements.append(
            Spacer(1, 20)
        )

        

        elements.append(
            Paragraph(
                "Defect Type Distribution",
                heading_style,
            )
        )

        defect_data = [
            ["Defect Type", "Count"]
        ]

        for defect, count in sorted(
            defect_distribution.items(),
            key=lambda item: item[1],
            reverse=True,
        ):

            defect_data.append(
                [
                    defect.replace(
                        "_",
                        " "
                    ).title(),
                    str(count),
                ]
            )

        if len(defect_data) == 1:

            defect_data.append(
                [
                    "No defect data available",
                    "0",
                ]
            )

        defect_table = Table(
            defect_data,
            colWidths=[250, 150],
        )

        defect_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1e293b"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        7,
                    ),
                ]
            )
        )

        elements.append(
            defect_table
        )

        elements.append(
            Spacer(1, 20)
        )

        

        elements.append(
            Paragraph(
                "Inspection Details",
                heading_style,
            )
        )

        inspection_data = [
            [
                "ID",
                "Date",
                "Result",
                "Defect",
                "Severity",
                "Action",
            ]
        ]

        for inspection in inspections:

            created_at = inspection.created_at

            if created_at:

                date_text = created_at.strftime(
                    "%Y-%m-%d"
                )

            else:

                date_text = "-"

            result_text = (
                "GOOD"
                if inspection.prediction == "PASS"
                else "DEFECT"
            )

            inspection_data.append(
                [
                    str(inspection.id),
                    date_text,
                    result_text,
                    (
                        inspection.defect_type
                        or "-"
                    ),
                    (
                        inspection.severity_level
                        or "-"
                    ),
                    (
                        inspection.recommended_action
                        or "-"
                    ),
                ]
            )

        inspection_table = Table(
            inspection_data,
            colWidths=[
                35,
                70,
                55,
                120,
                65,
                75,
            ],
            repeatRows=1,
        )

        inspection_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1e293b"),
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey,
                    ),
                    (
                        "PADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        elements.append(
            inspection_table
        )

        

        document.build(
            elements
        )

        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="quality_report_{days}days.pdf"'
                )
            },
        )

    finally:

        db.close()




@app.get(
    "/reports/quality-summary/csv"
)
def quality_summary_csv(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    if days not in [7, 30, 90]:

        raise HTTPException(
            status_code=400,
            detail="Days must be one of: 7, 30, or 90",
        )

    end_date = datetime.now(
        timezone.utc
    )

    start_date = (
        end_date
        - timedelta(days=days)
    )

    inspections = (
        db.query(Inspection)
        .filter(
            Inspection.created_at >= start_date,
            Inspection.created_at <= end_date,
        )
        .order_by(
            Inspection.created_at.desc()
        )
        .all()
    )

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        ["VisionInspect AI - Quality Report"]
    )

    writer.writerow(
        [f"Period: Last {days} days"]
    )

    writer.writerow([])

    total_inspections = len(
        inspections
    )

    passed = 0
    failed = 0
    rework = 0
    review = 0
    manual_review = 0

    defect_distribution = {}

    severity_distribution = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
    }

    for inspection in inspections:

        action = (
            inspection.recommended_action
        )

        if action == "Reject":
            failed += 1

        elif action == "Rework":
            rework += 1

        elif action == "Review":
            review += 1

        elif (
            inspection.prediction == "PASS"
            or action == "Accept"
        ):
            passed += 1

        if inspection.manual_review:
            manual_review += 1

        if inspection.defect_type:

            defect_distribution[
                inspection.defect_type
            ] = (
                defect_distribution.get(
                    inspection.defect_type,
                    0,
                )
                + 1
            )

        if inspection.severity_level:

            if (
                inspection.severity_level
                in severity_distribution
            ):

                severity_distribution[
                    inspection.severity_level
                ] += 1

    quality_decided = (
        passed
        + failed
        + rework
        + review
    )

    pass_rate = (
        (passed / quality_decided) * 100
        if quality_decided
        else 0
    )

    defect_rate = (
        (
            (
                failed
                + rework
                + review
            )
            / quality_decided
        )
        * 100
        if quality_decided
        else 0
    )

    writer.writerow(
        ["Metric", "Value"]
    )

    writer.writerow(
        [
            "Total Inspections",
            total_inspections,
        ]
    )

    writer.writerow(
        [
            "Quality Decided Inspections",
            quality_decided,
        ]
    )

    writer.writerow(
        ["Passed", passed]
    )

    writer.writerow(
        ["Failed", failed]
    )

    writer.writerow(
        ["Rework", rework]
    )

    writer.writerow(
        ["Review", review]
    )

    writer.writerow(
        ["Manual Review", manual_review]
    )

    writer.writerow(
        [
            "Pass Rate (%)",
            round(pass_rate, 2),
        ]
    )

    writer.writerow(
        [
            "Defect Rate (%)",
            round(defect_rate, 2),
        ]
    )

    writer.writerow([])

    writer.writerow(
        ["Defect Distribution"]
    )

    writer.writerow(
        ["Defect Type", "Count"]
    )

    for defect_type, count in sorted(
        defect_distribution.items()
    ):

        writer.writerow([
            defect_type,
            count,
        ])

    writer.writerow([])

    writer.writerow(
        ["Severity Distribution"]
    )

    writer.writerow(
        ["Severity Level", "Count"]
    )

    for level, count in (
        severity_distribution.items()
    ):

        writer.writerow([
            level,
            count,
        ])

    writer.writerow([])

    writer.writerow(
        ["Inspection Details"]
    )

    writer.writerow([
        "Inspection ID",
        "Date",
        "Product Category",
        "Prediction",
        "Defect Type",
        "Classification Confidence",
        "Severity Score",
        "Severity Level",
        "Recommended Action",
        "Manual Review",
        "Inspected By",
    ])

    for inspection in inspections:

        inspected_by = (
            db.query(User)
            .filter(
                User.id
                == inspection.user_id
            )
            .first()
        )

        inspected_by_name = (
            inspected_by.name
            if inspected_by
            else "Unknown"
        )

        writer.writerow([
            inspection.id,
            inspection.created_at,
            inspection.product_category,
            inspection.prediction,
            inspection.defect_type,
            inspection.classification_confidence,
            inspection.severity_score,
            inspection.severity_level,
            inspection.recommended_action,
            inspection.manual_review,
            inspected_by_name,
        ])

    output.seek(0)

    filename = (
        f"quality_report_{days}_days.csv"
    )

    return StreamingResponse(
        iter([
            output.getvalue()
        ]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}"'
        },
    )



@app.get("/analytics/summary")
def analytics_summary(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    if days not in [7, 30, 90]:

        raise HTTPException(
            status_code=400,
            detail="Days must be one of: 7, 30, or 90",
        )

    end_date = datetime.now(
        timezone.utc
    )

    start_date = (
        end_date
        - timedelta(days=days)
    )

    inspections = (
        db.query(Inspection)
        .filter(
            Inspection.created_at >= start_date,
            Inspection.created_at <= end_date,
        )
        .order_by(
            Inspection.created_at.asc()
        )
        .all()
    )

    total_inspections = len(
        inspections
    )

    passed = 0
    failed = 0
    rework = 0
    review = 0
    manual_review = 0

    defect_distribution = {}

    severity_distribution = {
        "Critical": 0,
        "High": 0,
        "Medium": 0,
        "Low": 0,
    }

    daily_data = {}

    
    confidence_distribution = {
        "<70%": 0,
        "70-79%": 0,
        "80-89%": 0,
        "90-100%": 0,
    }

    for inspection in inspections:

        action = (
            inspection.recommended_action
        )

        if action == "Reject":

            failed += 1

        elif action == "Rework":

            rework += 1

        elif action == "Review":

            review += 1

        elif (
            inspection.prediction == "PASS"
            or action == "Accept"
        ):

            passed += 1

        if inspection.manual_review:

            manual_review += 1

        if inspection.defect_type:

            defect_distribution[
                inspection.defect_type
            ] = (
                defect_distribution.get(
                    inspection.defect_type,
                    0,
                )
                + 1
            )

        if inspection.severity_level:

            if (
                inspection.severity_level
                in severity_distribution
            ):

                severity_distribution[
                    inspection.severity_level
                ] += 1

        if inspection.created_at:

            date_key = (
                inspection.created_at
                .date()
                .isoformat()
            )

            if date_key not in daily_data:

                daily_data[date_key] = {
                    "date": date_key,
                    "inspections": 0,
                    "passed": 0,
                    "failed": 0,
                    "rework": 0,
                    "review": 0,
                }

            daily_data[
                date_key
            ]["inspections"] += 1

            if action == "Reject":

                daily_data[
                    date_key
                ]["failed"] += 1

            elif action == "Rework":

                daily_data[
                    date_key
                ]["rework"] += 1

            elif action == "Review":

                daily_data[
                    date_key
                ]["review"] += 1

            elif (
                inspection.prediction
                == "PASS"
                or action == "Accept"
            ):

                daily_data[
                    date_key
                ]["passed"] += 1

        
        if inspection.classification_confidence is not None:

            confidence = (
                inspection.classification_confidence
            )

            if confidence < 70:

                confidence_distribution[
                    "<70%"
                ] += 1

            elif confidence < 80:

                confidence_distribution[
                    "70-79%"
                ] += 1

            elif confidence < 90:

                confidence_distribution[
                    "80-89%"
                ] += 1

            else:

                confidence_distribution[
                    "90-100%"
                ] += 1

    quality_decided = (
        passed
        + failed
        + rework
        + review
    )

    pass_rate = (
        (passed / quality_decided)
        * 100
        if quality_decided
        else 0
    )

    defect_rate = (
        (
            (
                failed
                + rework
                + review
            )
            / quality_decided
        )
        * 100
        if quality_decided
        else 0
    )

    daily_trend = list(
        daily_data.values()
    )

    daily_trend.sort(
        key=lambda x: x["date"]
    )

    return {
        "period_days": days,

        "total_inspections":
            total_inspections,

        "quality_decided_inspections":
            quality_decided,

        "passed":
            passed,

        "failed":
            failed,

        "rework":
            rework,

        "review":
            review,

        "manual_review":
            manual_review,

        "pass_rate":
            round(
                pass_rate,
                2,
            ),

        "defect_rate":
            round(
                defect_rate,
                2,
            ),

        "daily_trend":
            daily_trend,

        "severity_distribution":
            severity_distribution,

        "defect_distribution":
            defect_distribution,

        

        "confidence_distribution":
            confidence_distribution,
    }




@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "VisionInspect AI",
    }