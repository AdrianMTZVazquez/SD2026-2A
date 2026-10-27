# gRPC entre dos computadoras

- **Equipo A**: corre el servidor y publica el puerto 50051 en su IP de LAN.
- **Equipo B**: corre el cliente y apunta a `<IP del equipo A>:50051`.

`server.py`, `client.py`, `saludo.proto` y el `Dockerfile` no cambian. El servidor
escucha en `0.0.0.0:50051` dentro del contenedor, y `ports: "50051:50051"` expone
ese puerto en todas las interfaces del equipo A.

```
Equipo B                                 Equipo A
cliente ──► 192.168.1.10:50051 ──LAN──►  host:50051 ──► contenedor servidor 0.0.0.0:50051
```

Requisitos: los dos equipos en la misma red (o con ruta entre ellos), Docker en ambos,
y el proyecto completo (`3_gRPC_Swarm/`) copiado en ambos, porque cada uno construye
la imagen `grpc-img` desde el `Dockerfile` de la raíz.

```
3_gRPC_Swarm/
  Dockerfile, saludo.proto, server.py, client.py, docker-compose.yml
  multihost/
    equipo_a/docker-compose.yml   servidor + ports 50051:50051
    equipo_b/docker-compose.yml   cliente con SERVIDOR=${SERVIDOR}
    equipo_b/.env.example
    prueba.py                     cliente de diagnóstico
    swarm/README.md               variante con Docker Swarm
```

## 1. Obtener la IP de LAN del equipo A

Windows (PowerShell):

```powershell
Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } |
  Select-Object InterfaceAlias, @{n='IP';e={$_.IPv4Address.IPAddress}}
```

(o `ipconfig` y buscar "Dirección IPv4" del adaptador Wi-Fi/Ethernet.)

Linux:

```bash
hostname -I            # todas las IPs
ip -4 addr show        # detalle por interfaz
ip route get 1.1.1.1   # la IP de salida aparece tras "src"
```

Mac:

```bash
ipconfig getifaddr en0   # Wi-Fi; en1 u otra si usas Ethernet
```

Ignora `127.0.0.1`, `172.17.x.x` (Docker), `192.168.56.x` (VirtualBox) y `100.x.x.x`
(VPN tipo Tailscale) salvo que esa sea la red que comparten los dos equipos.

## 2. Abrir el puerto 50051 en el firewall del equipo A

Windows (PowerShell como administrador):

```powershell
New-NetFirewallRule -DisplayName "gRPC 50051" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow
```

Si la red está marcada como "Pública", Windows es más restrictivo. Para ver el perfil
y cambiarlo a privada:

```powershell
Get-NetConnectionProfile
Set-NetConnectionProfile -InterfaceAlias "Wi-Fi" -NetworkCategory Private
```

Linux (ufw):

```bash
sudo ufw allow 50051/tcp
sudo ufw status
```

Para quitar la regla al terminar:

```powershell
Remove-NetFirewallRule -DisplayName "gRPC 50051"
```

```bash
sudo ufw delete allow 50051/tcp
```

## 3. Equipo A: levantar el servidor

```bash
cd multihost/equipo_a
docker compose up -d --build
docker compose logs -f
```

Debe aparecer `Servidor gRPC escuchando en el puerto 50051`. Prueba local con la IP de LAN
(no `localhost`), para confirmar que el puerto está publicado en esa interfaz:

```bash
python ../prueba.py 192.168.1.10:50051
```

## 4. Equipo B: correr el cliente

Copia `.env.example` a `.env` y pon la IP del equipo A:

PowerShell:

```powershell
cd multihost\equipo_b
Copy-Item .env.example .env
notepad .env          # SERVIDOR=<IP del equipo A>:50051
docker compose up --build
```

bash:

```bash
cd multihost/equipo_b
cp .env.example .env
nano .env             # SERVIDOR=<IP del equipo A>:50051
docker compose up --build
```

También se puede pasar sin `.env`:

```powershell
$env:SERVIDOR = "192.168.1.10:50051"; docker compose up --build
```

```bash
SERVIDOR=192.168.1.10:50051 docker compose up --build
```

Salida esperada:

```
cliente-1  | 0: Hola <id cliente> #0, soy <id del contenedor servidor>
cliente-1  | 1: Hola <id cliente> #1, soy <id del contenedor servidor>
...
```

El id tras `soy` coincide con `docker ps` en el equipo A. El cliente corre en bucle;
`Ctrl+C` para detenerlo (o `docker compose up -d` y `docker compose logs -f`).

## 5. prueba.py: cliente de diagnóstico

Corre en el host (sin Docker). Instalar dependencias una vez:

```bash
pip install grpcio grpcio-tools
```

```bash
python prueba.py 192.168.1.10:50051
```

| Salida | Significado |
|--------|-------------|
| `OK: Hola ..., soy <id>` | Todo funciona |
| `DEADLINE_EXCEEDED` | No hubo conexión en 4 s: IP equivocada, firewall, contenedor caído, o el servidor escucha en `127.0.0.1` |
| `UNAVAILABLE` | Conexión rechazada o no resoluble de forma definitiva |
| `UNIMPLEMENTED` | Hay algo en el puerto, pero no es este servicio |

Con `wait_for_ready=True`, gRPC reintenta mientras el canal no conecta, así que la
mayoría de fallos de red aparecen como `DEADLINE_EXCEEDED` y no como `UNAVAILABLE`.

## 6. Diagnóstico por capas

Ve de abajo hacia arriba; no pases a la siguiente capa hasta que la anterior funcione.

**Capa 1: red (¿B ve a A?)**

```bash
ping 192.168.1.10
```

Windows bloquea ICMP por defecto: un `ping` fallido hacia un Windows no prueba nada
por sí solo. Pasa a la capa 2.

**Capa 2: puerto TCP (¿el 50051 de A acepta conexiones desde B?)**

PowerShell:

```powershell
Test-NetConnection 192.168.1.10 -Port 50051
# TcpTestSucceeded : True
```

bash:

```bash
nc -vz 192.168.1.10 50051
# Connection to 192.168.1.10 50051 port [tcp/*] succeeded!
```

Si falla: firewall del equipo A, contenedor no corriendo, o red de invitados con
aislamiento entre clientes (común en Wi-Fi de universidades y hoteles).

**Capa 3: contenedor (en el equipo A)**

```bash
docker ps
# grpc-img ... 0.0.0.0:50051->50051/tcp
```

Si la columna PORTS está vacía, falta `ports:` en el compose. Si dice
`127.0.0.1:50051->50051/tcp`, solo se publicó en loopback.

**Capa 4: aplicación**

```bash
docker logs <id o nombre del contenedor>
# Servidor gRPC escuchando en el puerto 50051
# Petición recibida de: <id cliente> #0   <- llegan peticiones
```

Si el puerto TCP abre (capa 2 OK) pero `prueba.py` da `DEADLINE_EXCEEDED` y no
aparece `Petición recibida`, el servidor probablemente escucha en `127.0.0.1`
dentro del contenedor (revisa `add_insecure_port` en `server.py`): Docker entrega
la conexión a la interfaz `eth0` del contenedor, no a su loopback, y nadie la atiende.

### Caso especial: Docker Desktop con WSL2 en modo `mirrored`

Si `%USERPROFILE%\.wslconfig` tiene `networkingMode=mirrored`, el puerto publicado
vive dentro de la VM de WSL y las conexiones a la IP de LAN pasan por el **firewall
de Hyper-V**, no por la regla de `New-NetFirewallRule`. Síntoma: `127.0.0.1:50051`
da `OK`, pero `<IP LAN>:50051` da `DEADLINE_EXCEEDED` y `Test-NetConnection` falla.

Comprobar (PowerShell):

```powershell
Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'
# DefaultInboundAction : Block  -> bloquea las conexiones entrantes desde la LAN
```

Permitir solo el 50051 (PowerShell como administrador):

```powershell
New-NetFirewallHyperVRule -Name "gRPC-50051" -DisplayName "gRPC 50051 (WSL)" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 50051 -Action Allow
# Quitarla:
Remove-NetFirewallHyperVRule -Name "gRPC-50051"
```

Para que el **mismo** equipo A pueda conectarse a su propia IP de LAN (prueba local
del paso 3), agrega a `.wslconfig` y reinicia WSL con `wsl --shutdown`:

```ini
[wsl2]
networkingMode=mirrored
[experimental]
hostAddressLoopback=true
```

## 7. Limpieza

```bash
# Equipo A
cd multihost/equipo_a && docker compose down
# Equipo B
cd multihost/equipo_b && docker compose down
```

## Alternativa: Docker Swarm

Red overlay entre los dos equipos, el cliente usa `servidor:50051` por nombre:
ver [swarm/README.md](swarm/README.md).
