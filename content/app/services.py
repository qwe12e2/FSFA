
from sqlalchemy.orm import Session
from app import models
from app.schemas import ControlResponse

class TemperatureController:
    def __init__(self, kp, ki, kd, output_min, output_max):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max
        self.integral = 0.0
        self.last_error = 0.0

    def calculate_setpoint(self, t_out, graph):
        if t_out <= graph.t_out_min:
            return graph.t_supply_min
        elif t_out >= graph.t_out_max:
            return graph.t_supply_max
        else:
            setpoint = graph.t_supply_max + (graph.t_supply_min - graph.t_supply_max) * (t_out - graph.t_out_max) / (graph.t_out_min - graph.t_out_max)
            return round(setpoint, 1)

    def update(self, setpoint, current_temp, dt):
        error = setpoint - current_temp
        p_term = self.kp * error
        self.integral += error * dt
        i_term = self.ki * self.integral
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        d_term = self.kd * derivative
        output = p_term + i_term + d_term
        output = max(self.output_min, min(self.output_max, output))
        if output <= self.output_min or output >= self.output_max:
            self.integral -= error * dt
        self.last_error = error
        return {
            "output_signal": round(output, 2),
            "p_term": round(p_term, 2),
            "i_term": round(i_term, 2),
            "d_term": round(d_term, 2),
            "error": round(error, 2)
        }

class ControlService:
    def __init__(self, db: Session):
        self.db = db
        self.current_mode = "AUTO"
        self.manual_output = 0.0
        self._load_active_settings()

    def _load_active_settings(self):
        pid = self.db.query(models.PIDSettings).filter(models.PIDSettings.is_active == True).first()
        if not pid:
            pid = models.PIDSettings()
            self.db.add(pid)
            self.db.commit()
            self.db.refresh(pid)
        graph = self.db.query(models.TemperatureGraph).filter(models.TemperatureGraph.is_active == True).first()
        if not graph:
            graph = models.TemperatureGraph()
            self.db.add(graph)
            self.db.commit()
            self.db.refresh(graph)
        self.active_pid = pid
        self.active_graph = graph
        self.controller = TemperatureController(pid.kp, pid.ki, pid.kd, pid.output_min, pid.output_max)

    def get_setpoint(self, t_out):
        return self.controller.calculate_setpoint(t_out, self.active_graph)

    def execute_control(self, t_out, t_current, dt=1.0):
        setpoint = self.get_setpoint(t_out)
        if self.current_mode == "AUTO":
            result = self.controller.update(setpoint, t_current, dt)
            output_signal = result["output_signal"]
            p_term = result["p_term"]
            i_term = result["i_term"]
            d_term = result["d_term"]
            error = result["error"]
        else:
            output_signal = self.manual_output
            p_term = i_term = d_term = 0.0
            error = setpoint - t_current

        log = models.ControlLog(
            mode=self.current_mode,
            t_out=t_out,
            t_current=t_current,
            setpoint=setpoint,
            error=error,
            p_term=p_term,
            i_term=i_term,
            d_term=d_term,
            output_signal=output_signal,
            manual_output=self.manual_output if self.current_mode == "MANUAL" else None,
            pid_settings_id=self.active_pid.id
        )
        self.db.add(log)
        self.db.commit()

        return ControlResponse(
            mode=self.current_mode,
            t_out=t_out,
            t_current=t_current,
            setpoint=setpoint,
            error=error,
            p_term=p_term,
            i_term=i_term,
            d_term=d_term,
            output_signal=output_signal,
            manual_output=self.manual_output if self.current_mode == "MANUAL" else None
        )

    def set_mode(self, mode):
        if mode.upper() in ["AUTO", "MANUAL"]:
            self.current_mode = mode.upper()
            if mode.upper() == "AUTO":
                self.controller.integral = 0.0
                self.controller.last_error = 0.0
            return True
        return False

    def set_manual_output(self, output):
        if 0 <= output <= 100:
            self.manual_output = output
            return True
        return False

    def get_batch_summary(self, hours=24):
        from datetime import datetime, timedelta
        since = datetime.utcnow() - timedelta(hours=hours)
        logs = self.db.query(models.ControlLog).filter(models.ControlLog.timestamp >= since).all()
        if not logs:
            return {"total": 0, "by_mode": {"AUTO": 0, "MANUAL": 0}, "avg_error": 0, "avg_output": 0}
        total = len(logs)
        auto_count = sum(1 for l in logs if l.mode == "AUTO")
        manual_count = total - auto_count
        avg_error = sum(abs(l.error) for l in logs) / total
        avg_output = sum(l.output_signal for l in logs) / total
        return {
            "total": total,
            "by_mode": {"AUTO": auto_count, "MANUAL": manual_count},
            "avg_error": round(avg_error, 2),
            "avg_output": round(avg_output, 2)
        }
