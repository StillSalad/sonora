import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,32}$")


class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32)
    display_name: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=10, max_length=128)
    confirm_min_age: bool

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        v = v.strip().lower()
        if not USERNAME_RE.match(v):
            raise ValueError("Usa 3–32 caratteri: lettere minuscole, numeri, punto o trattino basso.")
        return v

    @field_validator("display_name")
    @classmethod
    def _display(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Il nome non può essere vuoto.")
        return v


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class DeleteAccountIn(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    username: str
    display_name: str
    avatar_url: str | None
    role: str
    is_private: bool
    created_at: datetime
