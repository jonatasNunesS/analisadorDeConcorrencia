FROM python:3.11-slim

LABEL maintainer="seu-email@example.com"
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# instalar dependências de SO necessárias (inclui Tk/Tkinter, compiladores para alguns pacotes)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc libpq-dev \
       tk-dev tcl-dev libgtk-3-0 libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# copiar requirements e instalar
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && if [ -s /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# copiar projeto
COPY . /app

EXPOSE 8000
CMD ["python", "manage.py", "run_analyzer"]
