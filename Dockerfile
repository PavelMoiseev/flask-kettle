# Базовый образ Python
FROM python:3.10.4-alpine

# Обновление pip
RUN pip install --upgrade pip

# Установка poetry
RUN pip install poetry

# Настройка переменных среды
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Работа с директориями приложения
WORKDIR /flask_kettle
COPY . .

# Установка зависимостей из pyproject.toml с помощью Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Запуск приложения
CMD ["python", "flask_kettle/app.py"]
