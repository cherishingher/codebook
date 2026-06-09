from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CampusCreate(BaseModel):
    name: str
    code: str
    address: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None


class StudentCreate(BaseModel):
    campus_id: int
    name: str
    student_no: str | None = None
    gender: str | None = None
    birthday: date | None = None
    phone: str | None = None


class TeacherCreate(BaseModel):
    campus_id: int
    name: str
    phone: str | None = None
    title: str | None = None


class CourseCreate(BaseModel):
    campus_id: int
    name: str
    subject: str | None = None
    default_duration: int = 90
    default_hour_cost: Decimal = Decimal("1.00")


class DeviceCreate(BaseModel):
    campus_id: int
    device_code: str
    name: str
    device_secret: str
    device_type: str = "mac_mini"
    location_type: str = "frontdesk"
    location_name: str | None = None
