# 代码路径: app/modules/verification/ocr/utils.py

import io
import re
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from app.modules.verification.ocr.passport.utils import process_passport

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from passporteye import read_mrz

from app.modules.verification.ocr.schemas import OCRResponse

logger = logging.getLogger("CheckEasyBackend.verification.ocr.utils")

def preprocess_image(image: Image.Image) -> Image.Image:
    try:
        gray_image = image.convert("L")
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced_image = enhancer.enhance(2.0)
        return enhanced_image.filter(ImageFilter.SHARPEN)
    except Exception as e:
        logger.error("Error during image preprocessing: %s", str(e), exc_info=True)
        raise

def extract_fields(text: str) -> Dict[str, Any]:
    extracted = {}
    patterns = {
        "name": r"Name\s*[:：]\s*(.+)",
        "document_number": r"(?:ID|Passport No\.?)[\s:：]*([\w\d]+)",
        "birth_date": r"(?:Birth(?:date)?|Date of birth)[:：]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3}\s+\d{4})",
        "expiry_date": r"(?:Expiry(?: Date)?|Date of expiry)[:：]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]{3}\s+\d{4})"
    }

    extracted = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted[field] = match_date(match.group(1).strip()) if 'date' in field else match.group(1).strip()

    return extracted

def match_date(date_str: str) -> Optional[str]:
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%Y%m%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None

async def process_document(
    file, doc_type: str, country: str, side: Optional[str] = None, user_id: Optional[int] = None
) -> Dict[str, Any]:
    try:
        if doc_type.lower() == "passport":
            return await process_passport(file)
        elif doc_type.lower() in ["driver_license", "id_card"]:
            return {"success": False, "message": f"OCR for {doc_type} is not implemented."}
        else:
            file_bytes = await file.read()
            image = Image.open(io.BytesIO(file_bytes))
            processed_image = preprocess_image(image)
            loop = asyncio.get_running_loop()
            ocr_text = await loop.run_in_executor(None, pytesseract.image_to_string, processed_image)

            if not ocr_text.strip():
                return {"success": False, "message": "OCR could not recognize any text. Please upload a clearer image."}

            extracted_data = extract_fields(ocr_text)
            cert_result = process_certificate_verification(extracted_data.get("expiry_date", ""), extracted_data.get("document_number", "unknown"))
            extracted_data["document_status"] = cert_result["status"]

            return {"success": True, "data": extracted_data, "message": cert_result["message"]}

    except Exception as e:
        logger.error("Exception in OCR processing: %s", str(e), exc_info=True)
        return {"success": False, "message": f"OCR processing error: {str(e)}"}

def process_certificate_verification(expiry_date: str, document_number: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    try:
        expiry_dt = datetime.fromisoformat(expiry_date).date()
        status = "valid" if expiry_dt >= datetime.utcnow().date() else "expired"
        message = "Document is valid." if status == "valid" else "Document recognized, but it is expired."
        return {"valid": status == "valid", "status": status, "message": message}
    except Exception as e:
        logger.error("Verification error: %s", str(e), exc_info=True)
        return {"valid": False, "status": "error", "message": f"Verification error: {str(e)}"}