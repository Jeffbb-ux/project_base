# 代码路径: app/modules/verification/ocr/schemas.py

from pydantic import BaseModel, Field, constr
from typing import Optional, Dict, Any
from enum import Enum

class DocumentValidityStatus(str, Enum):
    valid = "valid"
    expired = "expired"
    unknown = "unknown"

class OCRUploadRequest(BaseModel):
    """
    上传请求数据模型：
    包含证件类型、证件国家和证件面向信息（例如：正面或反面）。
    注意：文件本身通常由 UploadFile 处理，此模型描述其他表单数据。
    """
    doc_type: constr(strip_whitespace=True, min_length=1, max_length=50) = Field(
        ...,
        description="证件类型，例如 '身份证'、'驾照'、'护照'（目前仅支持护照）",
        example="护照"
    )
    country: constr(strip_whitespace=True, min_length=1, max_length=50) = Field(
        ...,
        description="证件所属国家",
        example="China"
    )
    side: Optional[constr(strip_whitespace=True, min_length=1, max_length=10)] = Field(
        None,
        description="证件面向，例如 'front'（仅适用于护照，仅处理正面）",
        example="front"
    )

class OCRResultData(BaseModel):
    """
    识别结果数据模型：
    包含从护照中提取的关键信息，如护照号、姓名、出生日期、有效期等，
    以及其他额外信息和完整的 OCR 识别文本。
    """
    document_number: Optional[str] = Field(
        None,
        description="护照号码",
        example="EJ4391314"
    )
    name: Optional[str] = Field(
        None,
        description="持证人姓名",
        example="CHEN, JIAHAO"
    )
    birth_date: Optional[str] = Field(  # 👈 修改为 str
        None,
        description="出生日期，ISO格式",
        example="1995-03-02"
    )
    expiry_date: Optional[str] = Field(
        None,
        description="护照有效期截止日期",
        example="2031-05-23"
    )
    additional_info: Optional[Dict[str, Any]] = Field(
        None,
        description="其他识别信息，例如国籍等",
        example={"nationality": "CHN"}
    )
    extracted_text: Optional[str] = Field(
        None,
        description="完整的 OCR 识别结果文本，便于人工核对",
        example="……"
    )
    document_status: Optional[DocumentValidityStatus] = Field(
        DocumentValidityStatus.unknown,
        description="护照状态：'valid'（有效）、'expired'（已过期）、'unknown'（未知）",
        example="valid"
    )

class OCRResponse(BaseModel):
    """
    响应数据模型：
    返回 OCR 识别结果，包括状态提示信息、处理状态、识别出的护照数据及下一步操作提示（如需上传反面）。
    """
    message: str = Field(
        ...,
        description="操作结果提示信息",
        example="OCR processing succeeded."
    )
    status: str = Field(
        ...,
        description="处理状态，例如 'success' 或 'failure'",
        example="success"
    )
    data: Optional[OCRResultData] = Field(
        None,
        description="识别出的护照信息数据，若处理失败则为空"
    )
    next_action: Optional[str] = Field(
        None,
        description="下一步操作提示，例如 'upload_back'（若仅识别正面且需要补充后面）",
        example="upload_back"
    )