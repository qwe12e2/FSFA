
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from app import models, schemas
from app.database import get_db
from app.services import ControlService

router = APIRouter()

# Настройка шаблонов
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

# ========== HTML страницы ==========

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Главная страница"""
    service = ControlService(db)
    summary = service.get_batch_summary(24)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "summary": summary}
    )

@router.get("/control", response_class=HTMLResponse)
async def control_page(request: Request, db: Session = Depends(get_db)):
    """Страница управления"""
    service = ControlService(db)
    settings = service.active_pid
    graph = service.active_graph

    return templates.TemplateResponse(
        "control.html",
        {
            "request": request,
            "mode": service.current_mode,
            "manual_output": service.manual_output,
            "settings": settings,
            "graph": graph
        }
    )

@router.get("/pid-settings", response_class=HTMLResponse)
async def pid_settings_page(request: Request, db: Session = Depends(get_db)):
    """Страница настройки ПИД-регулятора"""
    pid = db.query(models.PIDSettings).filter(
        models.PIDSettings.is_active == True
    ).first()

    return templates.TemplateResponse(
        "pid_settings.html",
        {"request": request, "pid": pid}
    )

@router.get("/graph-settings", response_class=HTMLResponse)
async def graph_settings_page(request: Request, db: Session = Depends(get_db)):
    """Страница настройки температурного графика"""
    graph = db.query(models.TemperatureGraph).filter(
        models.TemperatureGraph.is_active == True
    ).first()

    return templates.TemplateResponse(
        "graph_settings.html",
        {"request": request, "graph": graph}
    )

@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, db: Session = Depends(get_db)):
    """Страница истории"""
    return templates.TemplateResponse(
        "history.html",
        {"request": request}
    )

# ========== API endpoints ==========

@router.get("/api/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "OK"}

@router.get("/api/pid-settings", response_model=schemas.PIDSettingsResponse)
async def get_pid_settings(db: Session = Depends(get_db)):
    """Получить активные настройки ПИД-регулятора"""
    pid = db.query(models.PIDSettings).filter(
        models.PIDSettings.is_active == True
    ).first()

    if not pid:
        raise HTTPException(status_code=404, detail="PID settings not found")

    return pid

@router.post("/api/pid-settings", response_model=schemas.PIDSettingsResponse)
async def update_pid_settings(
    settings: schemas.PIDSettingsCreate,
    db: Session = Depends(get_db)
):
    """Обновить настройки ПИД-регулятора"""
    # Деактивируем старые настройки
    db.query(models.PIDSettings).update({"is_active": False})

    # Создаем новые
    new_settings = models.PIDSettings(**settings.model_dump(), is_active=True)
    db.add(new_settings)
    db.commit()
    db.refresh(new_settings)

    return new_settings

@router.get("/api/temperature-graph", response_model=schemas.TemperatureGraphResponse)
async def get_temperature_graph(db: Session = Depends(get_db)):
    """Получить активные настройки температурного графика"""
    graph = db.query(models.TemperatureGraph).filter(
        models.TemperatureGraph.is_active == True
    ).first()

    if not graph:
        raise HTTPException(status_code=404, detail="Temperature graph not found")

    return graph

@router.post("/api/temperature-graph", response_model=schemas.TemperatureGraphResponse)
async def update_temperature_graph(
    graph_data: schemas.TemperatureGraphCreate,
    db: Session = Depends(get_db)
):
    """Обновить настройки температурного графика"""
    # Валидация
    if graph_data.t_out_min >= graph_data.t_out_max:
        raise HTTPException(
            status_code=400,
            detail="t_out_min must be less than t_out_max"
        )

    # Деактивируем старые настройки
    db.query(models.TemperatureGraph).update({"is_active": False})

    # Создаем новые
    new_graph = models.TemperatureGraph(**graph_data.model_dump(), is_active=True)
    db.add(new_graph)
    db.commit()
    db.refresh(new_graph)

    return new_graph

@router.post("/api/control/execute", response_model=schemas.ControlResponse)
async def execute_control(
    request: schemas.ControlRequest,
    db: Session = Depends(get_db)
):
    """Выполнить цикл управления"""
    service = ControlService(db)
    result = service.execute_control(request.t_out, request.t_current, request.dt)
    return result

@router.get("/api/control/mode")
async def get_control_mode(db: Session = Depends(get_db)):
    """Получить текущий режим управления"""
    service = ControlService(db)
    return {"mode": service.current_mode, "manual_output": service.manual_output}

@router.post("/api/control/mode/{mode}")
async def set_control_mode(mode: str, db: Session = Depends(get_db)):
    """Установить режим управления"""
    service = ControlService(db)
    if service.set_mode(mode):
        return {"mode": service.current_mode}
    raise HTTPException(status_code=400, detail="Invalid mode. Use AUTO or MANUAL")

@router.post("/api/control/manual")
async def set_manual_output(
    request: schemas.ManualControlRequest,
    db: Session = Depends(get_db)
):
    """Установить выходной сигнал в ручном режиме"""
    service = ControlService(db)
    if service.set_manual_output(request.output_signal):
        return {"manual_output": service.manual_output}
    raise HTTPException(status_code=400, detail="Output must be between 0 and 100")

@router.get("/api/control/history", response_model=List[schemas.ControlLogResponse])
async def get_control_history(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить историю управления"""
    logs = db.query(models.ControlLog).order_by(
        models.ControlLog.timestamp.desc()
    ).limit(limit).all()
    return logs

@router.get("/api/control/batch-summary")
async def get_batch_summary(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Получить сводку за период"""
    service = ControlService(db)
    return service.get_batch_summary(hours)

@router.get("/api/alarms")
async def get_alarms(
    limit: int = 50,
    acknowledged: bool = None,
    db: Session = Depends(get_db)
):
    """Получить аварийные события"""
    query = db.query(models.Alarm).order_by(models.Alarm.timestamp.desc())

    if acknowledged is not None:
        query = query.filter(models.Alarm.is_acknowledged == acknowledged)

    alarms = query.limit(limit).all()

    return [
        {
            "id": a.id,
            "timestamp": a.timestamp,
            "alarm_type": a.alarm_type,
            "message": a.message,
            "value": a.value,
            "is_acknowledged": a.is_acknowledged
        }
        for a in alarms
    ]

@router.post("/api/alarms/{alarm_id}/acknowledge")
async def acknowledge_alarm(alarm_id: int, db: Session = Depends(get_db)):
    """Подтвердить аварию"""
    alarm = db.query(models.Alarm).filter(models.Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarm.is_acknowledged = True
    alarm.acknowledged_at = datetime.utcnow()
    db.commit()

    return {"message": "Alarm acknowledged"}
