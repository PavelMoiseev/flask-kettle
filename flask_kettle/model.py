import sqlite3
import datetime


# Функция создания базы данных и таблицы
def create_db():
    # Установить соединение с базой данных
    conn = sqlite3.connect('kettle.db')
    c = conn.cursor()

    # Создать таблицу status, если она не существует
    c.execute('''CREATE TABLE IF NOT EXISTS status
                (datetime text, status text)''')

    # Сохранить изменения и закрыть соединение
    conn.commit()
    conn.close()


# Функция для добавления статуса в базу данных
def add_status_to_db(status):
    # Установить соединение с базой данных
    conn = sqlite3.connect('kettle.db')
    c = conn.cursor()

    # Добавить запись о статусе в базу данных
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO status (datetime, status) VALUES (?, ?)",
              (current_time, status))

    # Сохранить изменения в базе данных и закрыть соединение
    conn.commit()
    conn.close()
