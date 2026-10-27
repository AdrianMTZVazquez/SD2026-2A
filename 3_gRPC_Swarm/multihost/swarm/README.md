# Variante con Docker Swarm (red overlay)

En lugar de publicar el puerto 50051 en el equipo A, los dos equipos forman un
swarm y comparten una red overlay. El cliente llega al servidor por **nombre de
contenedor** (`servidor:50051`), igual que en la red `grpc-net` local.

## Puertos que deben estar abiertos entre los equipos

| Puerto | Protocolo | Uso |
|--------|-----------|-----|
| 2377   | TCP       | Gestión del clúster (solo hacia el manager) |
| 7946   | TCP y UDP | Descubrimiento de nodos (gossip) |
| 4789   | UDP       | Tráfico de la red overlay (VXLAN) |

Windows (PowerShell como administrador), en ambos equipos:

```powershell
New-NetFirewallRule -DisplayName "Swarm 2377" -Direction Inbound -Protocol TCP -LocalPort 2377 -Action Allow
New-NetFirewallRule -DisplayName "Swarm 7946 TCP" -Direction Inbound -Protocol TCP -LocalPort 7946 -Action Allow
New-NetFirewallRule -DisplayName "Swarm 7946 UDP" -Direction Inbound -Protocol UDP -LocalPort 7946 -Action Allow
New-NetFirewallRule -DisplayName "Swarm 4789 UDP" -Direction Inbound -Protocol UDP -LocalPort 4789 -Action Allow
```

Linux (ufw), en ambos equipos:

```bash
sudo ufw allow 2377/tcp
sudo ufw allow 7946/tcp
sudo ufw allow 7946/udp
sudo ufw allow 4789/udp
```

> Docker Desktop (Windows/Mac) corre el motor dentro de una VM, y el overlay
> entre dos Docker Desktop suele fallar. Para Swarm entre equipos usa Linux con
> Docker Engine nativo (o WSL2 con Docker Engine y red en modo *mirrored*).

## 1. Equipo A: crear el swarm (manager)

`--advertise-addr` es la IP de LAN del equipo A, la que el equipo B puede alcanzar:

```bash
docker swarm init --advertise-addr 192.168.1.10
```

La salida imprime el comando `join` con un token. Para verlo de nuevo:

```bash
docker swarm join-token worker
```

## 2. Equipo B: unirse

```bash
docker swarm join --token SWMTKN-1-xxxxx 192.168.1.10:2377
```

Comprobar en el equipo A:

```bash
docker node ls
```

## 3. Equipo A: red overlay attachable

`--attachable` permite conectar contenedores normales (`docker run`), no solo servicios:

```bash
docker network create --driver overlay --attachable grpc-overlay
```

## 4. Construir la imagen en ambos equipos

Desde la carpeta del proyecto (`3_gRPC_Swarm/`), en **cada** equipo, porque no
hay registro compartido:

```bash
docker build -t grpc-img .
```

## 5. Equipo A: servidor

```bash
docker run -d --name servidor --network grpc-overlay grpc-img python3 server.py
```

No hace falta `-p 50051:50051`: el tráfico va por la overlay.

## 6. Equipo B: cliente

```bash
docker run --rm --network grpc-overlay -e SERVIDOR=servidor:50051 grpc-img python3 client.py
```

La red overlay aparece en el equipo B cuando un contenedor se conecta a ella.
El cliente corre en bucle; `Ctrl+C` lo detiene. Salida esperada (sin `--hostname`,
`soy` muestra el id del contenedor servidor):

```
0: Hola <id cliente> #0, soy <id del contenedor servidor>
1: Hola <id cliente> #1, soy <id del contenedor servidor>
...
```

## Diagnóstico

```bash
docker node ls                                  # ¿ambos nodos Ready?
docker network inspect grpc-overlay             # ¿contenedores conectados?
docker run --rm --network grpc-overlay busybox nslookup servidor
docker logs servidor
```

Si `nslookup` resuelve pero la llamada da `DEADLINE_EXCEEDED`, revisa 4789/udp.

## Limpieza

```bash
# Equipo A
docker rm -f servidor
docker network rm grpc-overlay
# Equipo B
docker swarm leave
# Equipo A (al final)
docker swarm leave --force
```
