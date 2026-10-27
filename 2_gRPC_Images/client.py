import os
import hashlib
import grpc
import imagenes_pb2
import imagenes_pb2_grpc

TAM = 64 * 1024   # 64 KB por fragmento

SERVER = os.environ.get("SERVIDOR")

def fragmentos(ruta):
    nombre = os.path.basename(ruta)
    with open(ruta, "rb") as f:
        while True:
            datos = f.read(TAM)
            if not datos:
                break
            yield imagenes_pb2.Fragmento(
                nombre=nombre, datos=datos)
 
def main(ruta):
    stub = imagenes_pb2_grpc.ImagenesStub(
        grpc.insecure_channel(SERVER))
    r = stub.Subir(fragmentos(ruta),
                   wait_for_ready=True)
