# Используем официальный образ Python 3.9
FROM python:3.9-slim

# Устанавливаем необходимые пакеты для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app
# Создание директории для логов
RUN mkdir -p /var/log/vk_sp_logs
# Копируем requirements.txt и устанавливаем зависимости
COPY vk_project/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY vk_project/ /app/
WORKDIR /app/vk_project
# Указываем команду запуска по умолчанию
CMD ["make"]
