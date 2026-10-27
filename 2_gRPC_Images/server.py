import os
import grpc
import imagenes_pb2
import imagenes_pb2_grpc
from concurrent import futures

class Imagenes(imagenes_pb2_grpc.ImagenesServicer):
    def Subir(self, request_iterator, context):
        nombre = ""
        buf = bytearray()
        n = 0
        for frag in request_iterator:
            nombre = nombre or frag.nombre
            buf.extend(frag.datos)
            n += 1
        nombre = os.path.basename(nombre)
        with open(os.path.join("recibidos", nombre),
                  "wb") as f:
            f.write(buf)
        sha = hashlib.sha256(buf).hexdigest()
        return imagenes_pb2.Resumen(
            nombre=nombre,
            bytes_recibidos=len(buf), sha256=sha)
