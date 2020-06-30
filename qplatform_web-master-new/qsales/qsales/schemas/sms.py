from typing import List, Optional, Union

from pydantic import EmailStr

from qsales.const import SMSType
from qsales.schemas.base import CustomBaseModel


class SMSIn(CustomBaseModel):
    smstype: SMSType
    phone: str


class EmailIn(CustomBaseModel):
    smstype: SMSType
    email: EmailStr
