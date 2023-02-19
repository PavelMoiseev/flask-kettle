import threading
import time
import json
import signal
import os
import logging
from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from

from model import create_db, add_status_to_db
from doc_files.swagger_config import template


app = Flask(__name__)
swagger = Swagger(app, template=template)

logging.basicConfig(filename="kettle.log", level=logging.INFO)

IS_ON = False               # Статус: включен/выключен
IS_PAUSED = False           # Стату паузы

# Получение параметров чайника
with open("config.json", "r") as f:
    config = json.load(f)

WATER_VOLUME = config.get("water_volume")                               # Максимальный объем воды
SWITCH_OFF_TEMPERATURE = config.get("switch_off_temperature", 100)      # Температура кипения
BOILING_TIME = config.get("boiling_time", 5)                            # Время кипения
WATER_LEVEL = 0                                                         # Уровень воды
STARTING_TEMPERATURE = 0                                                # Начальная температура воды

# Логирование
def log_status(status):
    app.logger.info(status)

def boil():
    global IS_ON, IS_PAUSED, WATER_LEVEL, STARTING_TEMPERATURE
    while IS_ON:
        if not IS_PAUSED:
            if STARTING_TEMPERATURE < SWITCH_OFF_TEMPERATURE:
                STARTING_TEMPERATURE += SWITCH_OFF_TEMPERATURE / BOILING_TIME
                status = f"Температура повышается, текущая температура: {STARTING_TEMPERATURE}"
                log_status(status)
                add_status_to_db(status)
                time.sleep(1)
            else:
                status = "Чайник закипел"
                log_status(status)
                add_status_to_db(status)
                stop_boil()
        else:
            time.sleep(1)


@app.route("/", methods=["GET"])
def api_overview():
    """
    API Overview
    ---
    responses:
        200:
            description: Обзор API
    """
    data = {
            "GET Swagger документация": "/apidocs",
            "POST Залить воды в чайник и указать начальную температуру": "/pour",
            "GET Начать кипячение": "/start",
            "GET Поставить кипячение на паузу": "/pause",
            "GET Возобновить кипячение": "/resume",
            "GET Выключить чайник": "/stop",
        }
    return jsonify(data)


@app.route("/pour", methods=["POST"])
@swag_from('doc_files/kettle_pour.yml')
def kettle_pour():     
    global WATER_LEVEL, STARTING_TEMPERATURE
    water_level_request = float(request.form["WATER_LEVEL"])
    STARTING_TEMPERATURE = int(request.form["STARTING_TEMPERATURE"])
    if 0.0 <= water_level_request <= WATER_VOLUME:
        WATER_LEVEL = water_level_request
        status = f"{WATER_LEVEL} л. сейчас в чайнике! Температура воды {STARTING_TEMPERATURE} градусов"
        log_status(status)
        add_status_to_db(status)
        return jsonify({"message": status})
    else:
        status = "Превышен максимальный объем воды!"
        log_status(status)
        add_status_to_db(status)
        return jsonify({"message": status})


@app.route("/start", methods=["GET"])
def start_boil():
    """
    Начать кипячение
    ---
    responses:
        200:
            description: Кипячение началось!
    """
    global IS_ON, WATER_LEVEL
    if WATER_LEVEL <= 0:
        status = "Попытка включить пустой чайник!"
        log_status(status)
        add_status_to_db(status)
        return jsonify({"message": status})
    IS_ON = True
    t = threading.Thread(target=boil)
    t.start()
    status = "Начало кипячения!"
    log_status(status)
    add_status_to_db(status)
    return jsonify({"message": status})


@app.route("/pause", methods=["GET"])
def pause_boil():
    """
    Кипячение на паузе
    ---
    responses:
        200:
            description: Пауза!
    """
    global IS_PAUSED
    IS_PAUSED = True
    status = "Процесс закипания поставлен на паузу!"
    log_status(status)
    add_status_to_db(status)
    return jsonify({"message": status})


@app.route("/resume", methods=["GET"])
def resume_boil():
    """
    Возобновить кипячение
    ---
    responses:
        200:
            description: Кипячение!
    """
    global IS_PAUSED
    IS_PAUSED = False
    status = "Процесс закипания продолжается!"
    log_status(status)
    add_status_to_db(status)
    return jsonify({"message": status})


@app.route("/stop", methods=["GET"])
def stop_boil():
    """
    Выключить чайник
    ---
    responses:
        200:
            description: Чайник выключен!
    """
    status = "Чайник выключен. Программа остановлена."
    log_status(status)
    add_status_to_db(status)
    sig = getattr(signal, "SIGKILL", signal.SIGTERM)
    os.kill(os.getpid(), sig)


if __name__ == "__main__":
    create_db()
    app.run(use_reloader=True)
