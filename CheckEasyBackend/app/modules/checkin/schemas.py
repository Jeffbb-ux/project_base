# File: CheckEasyBackend/app/modules/checkin/schemas.py

from pydantic import BaseModel, Field, constr, field_validator
from datetime import datetime
from typing import Optional, Dict, Any

class CheckinRequest(BaseModel):
    """
    入住请求数据模型：
    包含必须字段：用户ID、证件ID（或证件类型+证件号码）、入住时间，
    以及可选字段：房间号、备注和其他附加信息。
    """
    user_id: int = Field(
        ..., 
        description="用户ID", 
        example=123
    )
    certificate_id: Optional[str] = Field(
        None,
        description="证件ID。如果提供此字段，则无需提供证件类型和证件号码。",
        example="CERT123456789"
    )
    certificate_type: Optional[constr(strip_whitespace=True, min_length=1)] = Field(
        None,
        description="证件类型，例如 '身份证'、'驾照'、'护照'。当未提供证件ID时，该字段必填。",
        example="身份证"
    )
    certificate_number: Optional[constr(strip_whitespace=True, min_length=1)] = Field(
        None,
        description="证件号码。当未提供证件ID时，该字段必填。",
        example="123456789012345678"
    )
    checkin_time: datetime = Field(
        ..., 
        description="入住时间（ISO 8601 格式）", 
        example="2025-03-05T14:30:00Z"
    )
    room_number: Optional[constr(strip_whitespace=True)] = Field(
        None, 
        description="房间号", 
        example="101"
    )
    remarks: Optional[str] = Field(
        None, 
        description="入住备注", 
        example="入住时带有额外行李"
    )
    additional_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="其他附加信息，如来源、特殊要求等", 
        example={"source": "mobile app"}
    )

    @field_validator("certificate_id", mode='after')
    def validate_certificate_info(cls, v, values):
        """
        校验逻辑：
          - 如果未提供 certificate_id，则必须同时提供 certificate_type 和 certificate_number。
        """
        if not v:
            if not values.get("certificate_type") or not values.get("certificate_number"):
                raise ValueError("必须提供证件ID，或者同时提供证件类型和证件号码。")
        return v

class CheckinResponse(BaseModel):
    """
    入住响应数据模型：
    返回入住操作的结果提示以及记录详细信息，
    包括入住记录ID、用户ID、用户姓名、证件信息、入住时间、房间号和备注等。
    """
    message: str = Field(
        ..., 
        description="入住结果提示信息", 
        example="Check-in successful"
    )
    checkin_id: int = Field(
        ..., 
        description="入住记录ID", 
        example=456
    )
    user_id: int = Field(
        ..., 
        description="用户ID", 
        example=123
    )
    user_name: str = Field(
        ..., 
        description="入住人姓名", 
        example="张三"
    )
    certificate_id: Optional[str] = Field(
        None,
        description="证件ID，如果在入住请求中提供了此字段，则原样返回",
        example="CERT123456789"
    )
    checkin_time: datetime = Field(
        ..., 
        description="入住时间", 
        example="2025-03-05T14:30:00Z"
    )
    room_number: Optional[str] = Field(
        None, 
        description="房间号", 
        example="101"
    )
    remarks: Optional[str] = Field(
        None, 
        description="入住备注", 
        example="入住时带有额外行李"
    )
    additional_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="其他附加信息", 
        example={"source": "mobile app"}
    )