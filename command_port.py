from collections import namedtuple
from contextlib import AbstractContextManager
import json
import socket
import threading
from queue import Queue, Empty

import bpy
from bpy.props import BoolProperty
from bpy.props import FloatProperty
from bpy.props import IntProperty

import warnings

# --- Stores result of command. Created to make easier detecting result from lines of stdout
ResultContainer = namedtuple("ResultContainer", ["value"])
COMMAND_PORT = None

import sys
sys.path.append(r"/home/pawel/git/tmp2")

try:
    import pydevd_pycharm
    pydevd_pycharm.settrace('localhost', port=6666, stdoutToServer=True, stderrToServer=True)
except ModuleNotFoundError:
    warnings.warn("Module 'pydevd_pycharm' not found, skipping pydevd_pycharm.settrace")

class OutputDuplicator(AbstractContextManager):
    """
    Context manager that can copy the output from stdout and send it to a queue that was passed to it.
    """

    def __init__(self, output_queue=None):
        self.real_stdout = sys.stdout
        self.output_queue = output_queue
        self.last_line = ''

    def __enter__(self):
        sys.stdout = self
        return self  # Result of a script

    def write(self, data):
        """ It makes possible for this class to replace the stdout """
        if not data or data in ["\r\n", "\n"]:
            return
        self.real_stdout.write(data)
        if self.output_queue is not None:
            self.output_queue.put(data)
        self.last_line = data

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.real_stdout


class CommandPort(threading.Thread):
    """ Command port runs on a separate thread """

    def __init__(self, queue_size=0, timeout=.1, port=5000, buffersize=4096, max_connections=5,
                 return_result=False, result_as_json=False, redirect_output=False, share_environ=True):
        super(CommandPort, self).__init__()

        self.do_run = True
        self.return_result = return_result
        self.result_as_json = result_as_json
        self.redirect_output = redirect_output
        self.buffersize = buffersize
        self.max_connections = max_connections
        self.share_environ = share_environ

        self.commands_queue = Queue(queue_size)
        self.output_queue = Queue(queue_size)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(timeout)
        self.socket.bind(('localhost', port))

    def run(self):
        # ---- Run while main thread of Blender is Alive
        # This feels a little bit hacky, but that was the most reliable way I've found
        # There's no method or callback that Blender calls on exit that could be used to close the port
        # So I'm detecting if a main thread of blender did finish working.
        # If it did, then I'm breaking the loop and closing the port.
        threads = threading.enumerate()
        while any([t.name == "MainThread" and t.is_alive() for t in threads]):
            if not self.do_run:
                # ---- Break also if user requested closing the port.
                print("do_run is False")
                break
            self.socket.listen(self.max_connections)
            try:
                connection, address = self.socket.accept()
                data = connection.recv(self.buffersize)
                size = sys.getsizeof(data)
                if size >= self.buffersize:
                    print("The length of input is probably too long: {}".format(size))
                if size >= 0:
                    command = data.decode()
                    self.commands_queue.put(command)
                    if self.redirect_output or self.return_result:
                        while True:
                            try:
                                output = self.output_queue.get_nowait()
                            except Empty:
                                continue
                            else:
                                if isinstance(output, ResultContainer):
                                    if self.result_as_json:
                                        result = json.dumps(output.value)
                                    else:
                                        result = str(output.value)
                                    connection.sendall(result.encode())
                                    break
                                elif output and output != "\n":
                                    connection.sendall(output.encode())
                    else:
                        connection.sendall('OK'.encode())
                    connection.shutdown(socket.SHUT_RDWR)
                    connection.close()
            except socket.timeout:
                pass
        self.socket.close()
        print("Closing the socket")
        return


class CommandPortOperator(bpy.types.Operator):
    """ Operator that runs in modal mode in main thread, checks if there are new commands to execute and runs them """

    bl_idname = "object.command_port"
    bl_label = "Blender Command Port"
    timer = None
    instance = None
    keep_command_port_running = False

    # noinspection PyUnusedLocal
    def __init__(self):
        super(CommandPortOperator, self).__init__()
        try:
            try:
                if not CommandPortOperator.instance.is_alive():
                    raise AttributeError  # Hacky, but works
                self.command_port = CommandPortOperator.instance
            except AttributeError:
                self.command_port = CommandPort(queue_size=bpy.context.window_manager.bcp_queue_size,
                                                timeout=bpy.context.window_manager.bcp_timeout,
                                                port=bpy.context.window_manager.bcp_port,
                                                buffersize=bpy.context.window_manager.bcp_buffersize,
                                                max_connections=bpy.context.window_manager.bcp_max_connections,
                                                return_result=bpy.context.window_manager.bcp_return_result,
                                                result_as_json=bpy.context.window_manager.bcp_result_as_json,
                                                redirect_output=bpy.context.window_manager.bcp_redirect_output,
                                                share_environ=bpy.context.window_manager.bcp_share_environ)
                CommandPortOperator.instance = self.command_port
                self.command_port.start()
        except AttributeError as e:
            try:
                # ---- Make sure that properties are not missing and did not cause this exception
                queue_size = bpy.context.window_manager.bcp_queue_size,
                timeout = bpy.context.window_manager.bcp_timeout,
                port = bpy.context.window_manager.bcp_port,
                buffersize = bpy.context.window_manager.bcp_buffersize,
                max_connections = bpy.context.window_manager.bcp_max_connections,
                return_result = bpy.context.window_manager.bcp_return_result,
                result_as_json = bpy.context.window_manager.bcp_result_as_json,
                redirect_output = bpy.context.window_manager.bcp_redirect_output
                bcp_share_environ = bpy.context.window_manager.bcp_share_environ
            except AttributeError:
                # ---- properties are missing
                raise AttributeError("Properties are not registered. "
                                     "Run 'register_properties' function before opening the port")
            # ---- If properties are working, then re-raise an exception
            raise e
        print("Command port opened")

    def check_property(self):
        if not CommandPortOperator.keep_command_port_running:
            self.close_port()

    def close_port(self):
        if self.timer is not None:
            bpy.context.window_manager.event_timer_remove(self.timer)
        print("Waiting for command port thread to end....")
        self.command_port.do_run = False
        while self.command_port.is_alive():
            pass
        print("Command port thread was stopped.")

    def execute(self, context):
        if not self.command_port.is_alive():
            return {'FINISHED'}
        try:
            command = self.command_port.commands_queue.get_nowait()
            if command:
                try:
                    if self.command_port.redirect_output:
                        output = self.command_port.output_queue
                    else:
                        output = None
                    with OutputDuplicator(output_queue=output) as output_duplicator:
                        if self.command_port.share_environ:
                            _locals = dict()
                            exec(command, globals(), _locals)
                            globals().update(_locals)
                        else:
                            exec(command, globals(), {})
                    result = output_duplicator.last_line
                except Exception as e:
                    result = '\n'.join([str(v) for v in e.args])
                self.command_port.output_queue.put(ResultContainer(value=result))
        except Empty:
            pass
        if self.timer is None:
            self.timer = context.window_manager.event_timer_add(.01, window=context.window)
        return {'PASS_THROUGH'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            self.execute(context)
            return {"RUNNING_MODAL"}
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        try:
            CommandPortOperator.keep_command_port_running = True
        except AttributeError:
            # --- Registering it here, because it has to run "check_property method
            bpy.types.WindowManager.keep_command_port_running = bpy.props.BoolProperty(
                name="My Property",
                update=lambda o, c: self.check_property()
            )
            CommandPortOperator.keep_command_port_running = True
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def register(queue_size=0, timeout=.1, port=5000, buffersize=4096, max_connections=5,
             return_result=True, result_as_json=False, redirect_output=True, share_environ=True):
    """
    Registers properties. Values of those properties will be used as settings of the command port
    All properties have "bcp_" prefix, like Blender Command Port

    :param queue_size: Size of commands queue: max number of commands that are waiting to be executed. 0 == no limit
    :type queue_size: int
    :param timeout: Maximum connection timeout, in seconds
    :type timeout: float
    :param port: Port for the socket
    :type port: int
    :param buffersize: Buffersize, in bytes, for socket
    :type buffersize: int
    :param max_connections: "backlog" parameter of socket "listen" method
    :type max_connections: int
    :param return_result: Indicates if result of command should be returned
    :type return_result: bool
    :param result_as_json: Indicates if result of command should be returned as a json string
    :type result_as_json: bool
    :param redirect_output: Indicates if output should be copied and sent
    :type redirect_output: bool
    :param share_environ: Indicates if executed commands should operate on new dict instance, or os.environ of program
    :type share_environ: bool
    """
    bpy.types.WindowManager.bcp_queue_size: IntProperty() = IntProperty(default=queue_size,
                                                      name="Queue size",
                                                      description="Size of commands queue: max number of "
                                                                  "commands that are qaiting to be executed. "
                                                                  "0 == no limit", )
    bpy.types.WindowManager.bcp_timeout: FloatProperty() = FloatProperty(default=timeout,
                                                       name="Timeout",
                                                       description="Maximum connection timeout, in seconds")
    bpy.types.WindowManager.bcp_port: IntProperty = IntProperty(default=port,
                                              name="Port",
                                              description="Port for the socket")
    bpy.types.WindowManager.bcp_buffersize: IntProperty = IntProperty(default=buffersize,
                                                    name="Buffersize",
                                                    description="Buffersize, in bytes, for socket")
    bpy.types.WindowManager.bcp_max_connections: IntProperty = IntProperty(default=max_connections,
                                                         name="Max connections",
                                                         description="\"backlog\" parameter of socket \"listen\" method")
    bpy.types.WindowManager.bcp_return_result: BoolProperty = BoolProperty(default=return_result,
                                                         name="Return result",
                                                         description="Indicates if result of command should be returned")
    bpy.types.WindowManager.bcp_result_as_json: BoolProperty = BoolProperty(default=result_as_json,
                                                          name="Result as json",
                                                          description="Indicates if result of command should be "
                                                                      "returned as a json string")
    bpy.types.WindowManager.bcp_redirect_output: BoolProperty = BoolProperty(default=redirect_output,
                                                           name="Redirect output",
                                                           description="Indicates if output should be copied and sent")
    bpy.types.WindowManager.bcp_share_environ: BoolProperty = BoolProperty(default=share_environ,
                                                         name="Share environment",
                                                         description="Indicates if current environment should share an "
                                                                     "application environment,\n"
                                                                     "or a new, clean one should be created "
                                                                     "for every executed command.\n"
                                                                     "If environment is shared,  then every module "
                                                                     "imported by command will be avaliable on "
                                                                     "application level, \n "
                                                                     "and forcommands executed later.")
    bpy.utils.register_class(CommandPortOperator)

def unregister():
    del bpy.types.WindowManager.bcp_queue_size
    del bpy.types.WindowManager.bcp_timeout
    del bpy.types.WindowManager.bcp_port
    del bpy.types.WindowManager.bcp_buffersize
    del bpy.types.WindowManager.bcp_max_connections
    del bpy.types.WindowManager.bcp_return_result
    del bpy.types.WindowManager.bcp_result_as_json
    del bpy.types.WindowManager.bcp_redirect_output
    del bpy.types.WindowManager.bcp_share_environ
    bpy.utils.unregister_class(CommandPortOperator)


if __name__ == "__main__":
    """ Copy&paste this file to Blender to start a command port in a simplest possible way """
    register()
    open_command_port()
