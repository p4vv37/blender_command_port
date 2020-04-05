import socket
import bpy
from command_port import CommandPortOperator


def queue_command(command, buffersize=None, port=None):
    """
    Add a command to commands queue of the command port.
    This function can be used like executeDeferred in Maya:
    * to run commands later, after current task or
    * to send command from a thread and evaluate in in the main thread of application safely.

    :param command: String with a command that will be executed
    :type command: unicode
    :param buffersize: Size of a socket buffer
    :type buffersize: int
    :param port: Port at which blender command port is working
    :type port: int
    """
    if port is None:
        port = bpy.context.window_manager.bcp_port
    if buffersize is None:
        buffersize = bpy.context.window_manager.bcp_buffersize

    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.connect(("127.0.0.1", port))

    soc.send(command.encode("ascii"))
    result_bytes = soc.recv(buffersize)
    result_string = result_bytes.decode("ascii")

    print("Result from server is {}".format(result_string))
