import socket
import sys
import os


def send_command(command):
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('localhost', int(sys.argv[2])))
    clientsocket.sendall(command.encode())
    while True:
        res = clientsocket.recv(4096)
        if not res:
            break
        print(res.decode())
    clientsocket.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Missing arguments.\n"
                           "syntax: python execute_file_in_blender.py \"path\\to\\file.py\" port_number")
    filepath = sys.argv[1]
    filename = os.path.basename(filepath)
    send_command("""exec(compile(open("{filepath}", "rb").read(), {filename}, 'exec'), globals, locals)""".format(
        filename=filename, filepath=filepath
    ))
