# 代码路径: app/modules/verification/ocr/passport/utils.py

import io
import logging
from datetime import datetime, date
from passporteye import read_mrz
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from typing import Optional

logger = logging.getLogger("CheckEasyBackend.verification.ocr.passport.utils")

def preprocess_image(image: Image.Image) -> Image.Image:
    try:
        gray_image = image.convert("L")
        enhancer = ImageEnhance.Contrast(gray_image)
        enhanced_image = enhancer.enhance(2.0)
        sharpened_image = enhanced_image.filter(ImageFilter.SHARPEN)
        return sharpened_image
    except Exception as e:
        logger.error("Error during image preprocessing: %s", str(e), exc_info=True)
        raise


# 在 passport/utils.py中明确定义 match_date()

from datetime import datetime
from typing import Optional

def match_date(date_str: str) -> Optional[str]:
    date_str = date_str.strip()
    date_formats = [
        "%Y-%m-%d",   # 2023-12-31
        "%d-%m-%Y",   # 31-12-2023
        "%m-%d-%Y",   # 12-31-2023
        "%Y%m%d",     # 20231231
        "%y%m%d",     # 231231 (YYMMDD)
        "%d %b %Y",   # 31 Dec 2023
        "%b %d %Y",   # Dec 31 2023
        "%d/%m/%Y",   # 31/12/2023
        "%m/%d/%Y",   # 12/31/2023
        "%d.%m.%Y",   # 31.12.2023
        "%m.%d.%Y",   # 12.31.2023
    ]

    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt).date()

            # 自动修正YY年份问题 (护照日期逻辑)
            if fmt == "%y%m%d":
                current_year = datetime.now().year % 100
                century = datetime.now().year - current_year
                if dt.year % 100 > current_year + 10:
                    dt = dt.replace(year=dt.year + century - 100)
                else:
                    dt = dt.replace(year=dt.year + century)
            return dt.isoformat()
        except ValueError:
            continue
    return None

def parse_mrz_date(date_str: str) -> Optional[str]:
    try:
        current_year = datetime.now().year % 100  # 新增这一行，解决未定义的问题
        if len(date_str) == 6:
            year, month, day = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:6])
            century = datetime.now().year - current_year
            if year > current_year + 10:
                year += century - 100
            else:
                year += century
            return datetime(year, month, day).date().isoformat()
        else:
            return None
    except ValueError as e:
        logger.error("Invalid MRZ date format: %s", date_str, exc_info=True)
        return None

def parse_date(date_str: str) -> Optional[str]:
    date_str = date_str.strip()
    formats = ["%y%m%d", "%Y%m%d"]
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            # YY年份特殊处理
            if fmt == "%y%m%d":
                current_year = datetime.now().year % 100
                year = parsed_date.year % 100
                century = datetime.now().year - current_year
                if year > current_year + 50:
                    parsed_date = parsed_date.replace(year=century - 100 + year)
                else:
                    parsed_date = parsed_date.replace(year=century + year)
            return parsed_date.isoformat()
        except ValueError:
            continue
    return None

async def process_passport(file) -> dict:
    try:
        # 确保只执行一次
        await file.seek(0)
        file_bytes = await file.read()

        # 第一次读取 MRZ
        image_stream = io.BytesIO(file_bytes)
        mrz = read_mrz(image_stream)

        if mrz is None or mrz.to_dict() is None:
            # 备用方案前明确重新创建image_stream对象
            logger.warning("PassportEye failed, fallback to preprocessing+pytesseract OCR.")
            fallback_image_stream = io.BytesIO(file_bytes)  # 重新创建image_stream，而非使用旧的
            image = Image.open(fallback_image_stream)
            processed_image = preprocess_image(image)

            ocr_text = pytesseract.image_to_string(processed_image)
            lines = [line for line in ocr_text.split('\n') if len(line.strip()) > 20 and '<' in line]

            if len(lines) >= 2:
                mrz_text = '\n'.join(lines[-2:])
                mrz = read_mrz(mrz_text, extra_cmdline_params="--oem 1")
            else:
                return {
                    "success": False,
                    "data": None,
                    "next_action": None,
                    "message": "Passport MRZ not detected clearly after fallback OCR."
                }

            if mrz is None or mrz.to_dict() is None:
                return {
                    "success": False,
                    "data": None,
                    "next_action": None,
                    "message": "Passport MRZ not recognized after fallback method."
                }

        mrz_data = mrz.to_dict()

        extracted_data = {
            "document_number": mrz_data.get("number"),
            "name": f"{mrz_data.get('surname', '')} {mrz_data.get('names', '')}".strip(),
            "birth_date": parse_mrz_date(mrz_data.get("date_of_birth")),
            "expiry_date": parse_mrz_date(mrz_data.get("expiration_date")),
            "additional_info": {
                "nationality": mrz_data.get("nationality"),
                "sex": mrz_data.get("sex"),
            },
            "extracted_text": str(mrz_data),
        }

        expiry_date_str = extracted_data.get("expiry_date")
        if expiry_date_str:
            expiry_date = datetime.fromisoformat(expiry_date_str).date()
            if expiry_date < datetime.utcnow().date():
                extracted_data["document_status"] = "expired"
                message = "Passport recognized successfully, but it is expired."
            else:
                extracted_data["document_status"] = "valid"
                message = "Passport recognized successfully."
        else:
            extracted_data["document_status"] = "unknown"
            message = "Passport recognized, but expiry date not found."

        return {
            "success": True,
            "data": extracted_data,
            "next_action": None,
            "message": message
        }

    except Exception as e:
        logger.error("Error in passport processing: %s", str(e), exc_info=True)
        return {
            "success": False,
            "data": None,
            "next_action": None,
            "message": f"Passport processing failed: {str(e)}"
        }