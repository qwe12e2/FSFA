
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app import models

def init_demo_data():
    db = SessionLocal()
    try:
        models.Base.metadata.create_all(bind=engine)
        db.query(models.PIDSettings).delete()
        db.query(models.TemperatureGraph).delete()
        db.query(models.ControlLog).delete()
        db.query(models.Alarm).delete()

        pid = models.PIDSettings(kp=0.8, ki=0.05, kd=0.1, output_min=0, output_max=100, is_active=True)
        graph = models.TemperatureGraph(t_out_min=-30, t_out_max=10, t_supply_min=95, t_supply_max=60, is_active=True)
        db.add(pid)
        db.add(graph)
        db.commit()
        print(" Демо-данные загружены")
    except Exception as e:
        print(f" Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_demo_data()
