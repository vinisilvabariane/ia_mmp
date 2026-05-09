FROM python:3.12-slim

# Evita geração de arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

# Mostra logs imediatamente
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala pipenv
RUN pip install --no-cache-dir pipenv

# Copia apenas dependências primeiro
# (melhora cache do Docker)
COPY Pipfile Pipfile.lock ./

# Instala dependências no sistema
RUN pipenv install --system --deploy

# Copia restante da aplicação
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]