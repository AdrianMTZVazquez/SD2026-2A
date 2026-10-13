# Buscar en DockerHub si existe un distro de linux específico
# O busca una ambiente para el docker
FROM ubuntu:latest

# Argumento al sistema operativo para que el GUI no cause problemas
ARG DEBIAN_FRONTEND=noninteractive

# Se instala Python
#   apt update 
RUN apt-get update && \
    apt-get install -y \
    python3 python3-pip \
    git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN git clone https://github.com/AdrianMTZVazquez/SD2026-2A.git

CMD ["sleep", "infinity"]
# CMD ["/bin/bash"]
# CMD ["python3", "RCDD_2026/main.py"]