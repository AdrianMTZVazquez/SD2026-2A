# 1_gRPC_Docker

Dos contenedores creados con la **misma imagen** que se comunican por **gRPC**:

- `servidor`: ejecuta `server.py` y escucha en el puerto `50051`.
- `cliente`: ejecuta `client.py` y cada segundo le manda una petición a `servidor:50051`.

Ambos están en la misma red de Docker (`grpc-net`), así que se encuentran por su nombre.

## Archivos

| Archivo | Qué hace |
|---|---|
| `saludo.proto` | Define el servicio `Saludo` y sus mensajes |
| `server.py` | Servidor gRPC |
| `client.py` | Cliente gRPC en un loop |
| `Dockerfile` | Imagen con Python + gRPC; genera `saludo_pb2*.py` al construir |
| `docker-compose.yml` | Levanta servidor y cliente en la misma red |

## Opción A: Docker Compose

```powershell
cd 1_gRPC_Docker
docker compose up --build        # Ctrl+C para detener
docker compose down              # borra contenedores y red
```

## Opción B: a mano con `docker run`

```powershell
cd 1_gRPC_Docker
docker build -t grpc-img .
docker network create grpc-net

docker run -d --name servidor --network grpc-net grpc-img python3 server.py
docker run -d --name cliente  --network grpc-net grpc-img python3 client.py

docker logs -f cliente           # ver las respuestas del servidor
docker logs -f servidor          # ver las peticiones recibidas
```

Para limpiar:

```powershell
docker rm -f servidor cliente
docker network rm grpc-net
```

## Opción C: entrando a los contenedores

```powershell
docker run -d --name servidor --network grpc-net grpc-img
docker run -d --name cliente  --network grpc-net grpc-img

docker exec -it servidor python3 server.py    # terminal 1
docker exec -it cliente  python3 client.py    # terminal 2
```

## Errores comunes

- El servidor debe escuchar en `0.0.0.0`, no en `localhost`.
- Los dos contenedores deben estar en la misma red (la red `bridge` por defecto no resuelve nombres).
- No hace falta `-p 50051:50051` para que se hablen entre contenedores; solo para entrar desde Windows.
