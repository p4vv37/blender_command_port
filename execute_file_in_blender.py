import socket
import sys
import os
import time


# noinspection PyUnboundLocalVariable
def send_command(command, host='localhost', port=None):
    if port is None:
        port = sys.argv[2]

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    e = ConnectionError("Max retries reached!")
    for i in range(3):
        # Retry 3 times, wait from 0 to .5 s. before retries, raise last Exception, if no success
        # noinspection PyBroadException
        try:
            clientsocket.connect((host, int(port)))
            break
        except Exception as e:
            time.sleep(i / 2.0)
    else:
        raise e
    clientsocket.sendall(command.encode())
    clientsocket.settimeout(1)
    result = ""
    while True:
        res = clientsocket.recv(4096)
        if not res:
            break
        print(res.decode())
        result += res.decode()
    clientsocket.shutdown(socket.SHUT_RDWR)
    clientsocket.close()
    return result


def execute_file(path, host='localhost', port=None):
    if port is None:
        port = sys.argv[2]

    filename = os.path.basename(path)
    result = send_command(
        """exec(compile(open(R"{filepath}").read(), "{filename}", "exec"), globals(), locals())""".format(filename=filename, filepath=path),
        host=host,
        port=port)
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError("Missing arguments.\n"
                           "syntax: python execute_file_in_blender.py \"path\\to\\file.py\" port_number")
    filepath = sys.argv[1]
    execute_file(filepath)
