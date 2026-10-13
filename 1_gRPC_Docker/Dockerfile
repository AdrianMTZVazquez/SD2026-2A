# Una sola imagen para servidor y cliente
FROM ubuntu:latest

# Argumento al sistema operativo para que el GUI no cause problemas
ARG DEBIAN_FRONTEND=noninteractive

# Se instala Python
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Se instala gRPC (--break-system-packages es necesario en Ubuntu reciente)
RUN pip3 install --break-system-packages grpcio grpcio-tools

# Para que los print se vean de inmediato en docker logs
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY saludo.proto server.py client.py ./

# Se genera el código de Python a partir del .proto
RUN python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. saludo.proto

CMD ["sleep", "infinity"]
