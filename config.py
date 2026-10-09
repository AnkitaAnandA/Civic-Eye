"""Shared choices and limits keep the UI, AI and database consistent."""
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
CATEGORIES = ["Pothole", "Garbage", "Damaged Road", "Streetlight", "Water Leakage", "Unknown"]
SEVERITIES = ["Low", "Medium", "High"]
STATUSES = ["Submitted", "In Progress", "Resolved"]
DEPARTMENTS = {
    "Pothole": "Roads & Infrastructure Department",
    "Damaged Road": "Roads & Infrastructure Department",
    "Garbage": "Solid Waste Management Department",
    "Streetlight": "Street Lighting / Electrical Department",
    "Water Leakage": "Water Supply & Sewerage Board",
    "Unknown": "Municipal Citizen Helpdesk",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
STRING_LIMITS = {"title": 80, "description": 2000, "visual_evidence": 500}
DB_PATH = BASE_DIR / "data" / "complaints.db"
UPLOAD_DIR = BASE_DIR / "uploads"

def demo_mode() -> bool:
    """Read the switch at call time so tests can change it safely."""
    return os.getenv("DEMO_MODE", "false").strip().lower() == "true"
