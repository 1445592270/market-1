from typing import List, Optional, Union

from pydantic import EmailStr

from qpweb.const import SMSType
from qpweb.schemas.base import CustomBaseModel


class SMSIn(CustomBaseModel):
    smstype: SMSType
    phone: str


class EmailIn(CustomBaseModel):
    smstype: SMSType
    email: EmailStr
