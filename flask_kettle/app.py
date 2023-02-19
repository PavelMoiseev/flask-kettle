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

is_on = False               # Статус: включен/выключен
is_paused = False           # Стату паузы

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
    global is_on, is_paused, water_level, STARTING_TEMPERATURE
    while is_on:
        if not is_paused:
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


@app.route("/pour", methods=["POST"])
@swag_from('doc_files/kettle_pour.yml')
def kettle_pour():     
    global water_level, STARTING_TEMPERATURE
    water_level_request = float(request.form["water_level"])
    STARTING_TEMPERATURE = int(request.form["STARTING_TEMPERATURE"])
    if 0.0 <= water_level_request <= WATER_VOLUME:
        WATER_LEVEL = water_level_request
        status = f"{water_level} л. сейчас в чайнике! Температура воды {STARTING_TEMPERATURE} градусов"
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
    global is_on, water_level
    if WATER_LEVEL <= 0:
        status = "Попытка включить пустой чайник!"
        log_status(status)
        add_status_to_db(status)
        return jsonify({"message": status})
    is_on = True
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
    global is_paused
    is_paused = True
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
    global is_paused
    is_paused = False
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
