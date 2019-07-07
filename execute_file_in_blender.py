import socket
import sys
import os


def send_command(command, host='localhost', port=None):
    if port is None:
        port = sys.argv[2]

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((host, int(port)))
    clientsocket.sendall(command.encode())
    result = ""
    while True:
        res = clientsocket.recv(4096)
        if not res:
            break
        print(res.decode())
        result += res.decode()
    clientsocket.close()
    return result


def execute_file(path, host='localhost', port=None):
    if port is None:
        port = sys.argv[2]

    filename = os.path.basename(path)
    result = send_command(
        """exec(compile(open("{filepath}", "rb").read(), "{filename}", 'exec'), globals(), locals())"""
            .format(filename=filename, filepath=path),
        host=host, port=port)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Missing arguments.\n"
                           "syntax: python execute_file_in_blender.py \"path\\to\\file.py\" port_number")
    filepath = sys.argv[1]
    execute_file(filepath)
