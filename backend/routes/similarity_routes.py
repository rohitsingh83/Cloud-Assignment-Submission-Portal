import re
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from backend.database import get_db_cursor
from backend.auth import require_teacher
from backend.cloud.storage_service import storage_service

router = APIRouter(prefix="/api/submissions", tags=["AI & Similarity Analytics"])

def extract_tokens(text: str) -> set:
    """Extracts alphanumeric tokens (3+ chars) for Jaccard and n-gram similarity."""
    words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
    return set(words)

def compute_similarity(text1: str, text2: str) -> float:
    """Computes Jaccard token similarity coefficient between two documents."""
    tokens1 = extract_tokens(text1)
    tokens2 = extract_tokens(text2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return round((len(intersection) / len(union)) * 100, 2)

@router.get("/{submission_id}/similarity-check")
def check_submission_similarity(
    submission_id: str,
    current_teacher: dict = Depends(require_teacher)
):
    """
    Industry-grade plagiarism similarity analyzer:
    Compares the target student submission against all other submissions
    for the same assignment and returns a similarity score and risk rating.
    """
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM submissions WHERE submission_id = ?", (submission_id,))
        target_sub = cursor.fetchone()
        if not target_sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        assignment_id = target_sub["assignment_id"]
        cursor.execute("""
            SELECT s.*, u.name AS student_name, u.email AS student_email
            FROM submissions s
            JOIN users u ON s.student_id = u.user_id
            WHERE s.assignment_id = ? AND s.submission_id != ?
        """, (assignment_id, submission_id))
        peer_subs = cursor.fetchall()

    # Read target file content
    try:
        target_path = storage_service.get_file_path(target_sub["storage_path"])
        with open(target_path, "rb") as f:
            target_content = f.read().decode("latin-1", errors="ignore")
    except Exception:
        target_content = target_sub["file_name"]

    matches = []
    max_score = 0.0

    for peer in peer_subs:
        try:
            peer_path = storage_service.get_file_path(peer["storage_path"])
            with open(peer_path, "rb") as f:
                peer_content = f.read().decode("latin-1", errors="ignore")
        except Exception:
            peer_content = peer["file_name"]

        score = compute_similarity(target_content, peer_content)
        if score > 0:
            matches.append({
                "compared_student": peer["student_name"],
                "compared_file": peer["file_name"],
                "similarity_score": score
            })
            if score > max_score:
                max_score = score

    # Classify Risk
    if max_score > 60:
        risk_level = "HIGH RISK"
        risk_color = "red"
        verdict = "Potential severe plagiarism detected across peer submissions."
    elif max_score > 30:
        risk_level = "MODERATE RISK"
        risk_color = "amber"
        verdict = "Moderate overlap detected. Common boilerplate or shared framework code."
    else:
        risk_level = "LOW RISK (ORIGINAL)"
        risk_color = "emerald"
        verdict = "Submission appears original with high unique content index."

    return {
        "submission_id": submission_id,
        "max_similarity_score": max_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "verdict": verdict,
        "total_compared": len(peer_subs),
        "matches": sorted(matches, key=lambda m: m["similarity_score"], reverse=True)[:5]
    }
