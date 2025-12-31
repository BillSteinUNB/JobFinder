"""Resume upload and profile endpoints."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from api.schemas import ResumeProfileResponse, ResumeUploadResponse
from src.processing.pdf_parser import PDFParseError, parse_resume_pdf, parse_resume_text
from src.processing.text_cleaner import extract_skills_simple

router = APIRouter()


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    preferred_location: str | None = Form(None),
    min_salary: float | None = Form(None),
) -> ResumeUploadResponse:
    """
    Upload a resume PDF and extract profile data.
    
    Creates embeddings for semantic job matching.
    """
    app_state = request.app.state.app_state
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Use PDF or TXT."
        )
    
    try:
        content = await file.read()
        
        if suffix == ".pdf":
            # Save to temp file for pdfplumber
            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            
            try:
                parsed = parse_resume_pdf(tmp_path)
                raw_text = parsed.text
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            # Plain text file
            raw_text = content.decode("utf-8")
        
        # Create resume profile with embedding
        profile = app_state.create_resume_profile(
            raw_text=raw_text,
            preferred_location=preferred_location,
            min_salary=min_salary,
        )
        
        # Extract skills for response
        skills = sorted(profile.skills)
        
        return ResumeUploadResponse(
            success=True,
            message=f"Resume processed: {len(skills)} skills extracted",
            profile=ResumeProfileResponse(
                fileName=file.filename,
                uploadedAt=None,  # Will be set by frontend
                skills=skills,
                experience=[],  # TODO: Extract from resume
                education=[],   # TODO: Extract from resume
                preferredLocation=preferred_location,
                minSalary=min_salary,
            )
        )
        
    except PDFParseError as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {e}")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File encoding not supported")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get("/profile", response_model=ResumeProfileResponse | None)
async def get_resume_profile(request: Request) -> ResumeProfileResponse | None:
    """Get the current resume profile if one has been uploaded."""
    app_state = request.app.state.app_state
    profile = app_state.resume_profile
    
    if profile is None:
        return None
    
    return ResumeProfileResponse(
        fileName=None,
        uploadedAt=None,
        skills=sorted(profile.skills),
        experience=[],
        education=[],
        preferredLocation=profile.preferred_location,
        minSalary=profile.min_salary,
    )
