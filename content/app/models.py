
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class PIDSettings(Base):
    __tablename__ = "pid_settings"

    id = Column(Integer, primary_key=True, index=True)
    kp = Column(Float, default=0.8)
    ki = Column(Float, default=0.05)
    kd = Column(Float, default=0.1)
    output_min = Column(Float, default=0.0)
    output_max = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    control_logs = relationship("ControlLog", back_populates="pid_settings")

class TemperatureGraph(Base):
    __tablename__ = "temperature_graph"

    id = Column(Integer, primary_key=True, index=True)
    t_out_min = Column(Float, default=-30.0)
    t_out_max = Column(Float, default=10.0)
    t_supply_min = Column(Float, default=95.0)
    t_supply_max = Column(Float, default=60.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ControlLog(Base):
    __tablename__ = "control_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    mode = Column(String, default="AUTO")
    t_out = Column(Float)
    t_current = Column(Float)
    setpoint = Column(Float)
    error = Column(Float)
    p_term = Column(Float)
    i_term = Column(Float)
    d_term = Column(Float)
    output_signal = Column(Float)
    manual_output = Column(Float, nullable=True)

    pid_settings_id = Column(Integer, ForeignKey("pid_settings.id"))
    pid_settings = relationship("PIDSettings", back_populates="control_logs")

class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    alarm_type = Column(String)
    message = Column(String)
    value = Column(Float)
    limit_min = Column(Float, nullable=True)
    limit_max = Column(Float, nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
