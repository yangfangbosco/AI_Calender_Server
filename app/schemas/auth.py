from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    family_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class JoinFamilyRequest(BaseModel):
    email: EmailStr
    password: str
    invite_code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    family_uuid: str
    invite_code: str


class DeviceRegisterRequest(BaseModel):
    device_type: str  # "tablet" or "phone"
    device_name: str | None = None
    push_token: str | None = None


class DeviceJoinRequest(BaseModel):
    invite_code: str
