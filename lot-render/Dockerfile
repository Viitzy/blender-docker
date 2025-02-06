FROM python:3.10-slim

# Install system dependencies required for Psycopg2 compilation
RUN apt-get update && apt-get install -y libpq-dev gcc 

# Defina o diretório de trabalho no contêiner
WORKDIR /app

# Adicionar PYTHONPATH
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Copy `messaging`,`shared` and `properties` directories into the container
COPY ./messaging /app/messaging
COPY ./shared /app/shared
COPY ./account /app/account

# Instale as dependências do projeto
RUN pip install --no-cache-dir -r account/requirements.txt

# Mudar para o diretório específico se necessário, por exemplo:
WORKDIR /app/account/src

# Comando para executar a aplicação usando o uvicorn, se aplicável
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


