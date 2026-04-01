
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app import models, database
from app.routes import router

# Создание таблиц БД
models.Base.metadata.create_all(bind=database.engine, checkfirst=True)

app = FastAPI(title="Boiler Temperature Control System", version="1.0.0")

# Подключение маршрутов
app.include_router(router)

# Статические файлы (если есть)
# В Colab, os.path.dirname(__file__) может быть недоступен при прямом запуске ячейки.
# Вместо этого, можно использовать os.getcwd() и указать относительный путь.
# Если app/main.py будет запускаться как самостоятельный скрипт, __file__ будет работать.
# Для целей Colab, сделаем путь относительным к текущей рабочей директории Colab.
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, "static")
# Убедимся, что директория app/templates существует для Jinja2
templates_dir = os.path.join(base_dir, "templates")

# Если папка 'static' не существует, FastAPI не смонтирует ее, это нормально.
# Для тестового запуска в Colab, мы можем создать фиктивную папку или пропустить монтирование,
# если реально статических файлов нет и это не критично для запуска API.
# Проверим, существует ли папка 'static' перед монтированием
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
