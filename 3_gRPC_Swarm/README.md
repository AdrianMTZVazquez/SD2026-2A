# 3_gRPC_Swarm

Copia de `1_gRPC_Docker` (mismos `saludo.proto`, `server.py`, `client.py`,
`Dockerfile` y `docker-compose.yml`) más la carpeta `multihost/` para correr el
servidor en una computadora y el cliente en otra.

- Una sola computadora: `docker compose up --build` (red `grpc-net`).
- Dos computadoras, puerto publicado: [multihost/README.md](multihost/README.md).
- Dos computadoras con Docker Swarm (red overlay): [multihost/swarm/README.md](multihost/swarm/README.md).
