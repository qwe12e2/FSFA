from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class PIDSettingsBase(BaseModel):
    kp: float = Field(0.8, ge=0, le=10)
    ki: float = Field(0.05, ge=0, le=5)
    kd: float = Field(0.1, ge=0, le=5)
    output_min: float = Field(0.0, ge=0, le=100)
    output_max: float = Field(100.0, ge=0, le=100)

class PIDSettingsCreate(PIDSettingsBase):
    pass

class PIDSettingsResponse(PIDSettingsBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TemperatureGraphBase(BaseModel):
    t_out_min: float = Field(-30.0, ge=-50, le=30)
    t_out_max: float = Field(10.0, ge=-30, le=50)
    t_supply_min: float = Field(95.0, ge=50, le=120)
    t_supply_max: float = Field(60.0, ge=30, le=100)

class TemperatureGraphCreate(TemperatureGraphBase):
    pass

class TemperatureGraphResponse(TemperatureGraphBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ControlRequest(BaseModel):
    t_out: float
    t_current: float
    dt: float = 1.0

class ControlResponse(BaseModel):
    mode: str
    t_out: float
    t_current: float
    setpoint: float
    error: float
    p_term: float
    i_term: float
    d_term: float
    output_signal: float
    manual_output: Optional[float] = None

class ManualControlRequest(BaseModel):
    output_signal: float = Field(..., ge=0, le=100)

class ControlLogResponse(BaseModel):
    id: int
    timestamp: datetime
    mode: str
    t_out: float
    t_current: float
    setpoint: float
    error: float
    output_signal: float

    class Config:
        from_attributes = True

class BatchSummary(BaseModel):
    total: int
    by_mode: dict
    avg_error: float
    avg_output: float
