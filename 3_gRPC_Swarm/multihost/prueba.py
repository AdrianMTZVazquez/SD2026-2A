"""Cliente de diagnóstico: python prueba.py <host:puerto>

Imprime "OK: <mensaje>" si el servidor responde, o el código de error gRPC
(UNAVAILABLE, DEADLINE_EXCEEDED, ...) si no.
Requiere: pip install grpcio grpcio-tools
"""
import os
import socket
import sys

import grpc

# saludo.proto está en la carpeta padre; se compila al vuelo
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
saludo_pb2, saludo_pb2_grpc = grpc.protos_and_services("saludo.proto")


def main():
    if len(sys.argv) != 2:
        print("Uso: python prueba.py <host:puerto>")
        sys.exit(2)
    destino = sys.argv[1]
    with grpc.insecure_channel(destino) as canal:
        stub = saludo_pb2_grpc.SaludoStub(canal)
        try:
            r = stub.Decir(
                saludo_pb2.Peticion(nombre=f"prueba@{socket.gethostname()}"),
                wait_for_ready=True,
                timeout=4,
            )
            print(f"OK: {r.mensaje}")
        except grpc.RpcError as e:
            print(e.code().name)
            sys.exit(1)


if __name__ == "__main__":
    main()
