bl_info = {
    "name": "Blender Command Port",
    "description": "Command Port implementation for blender. "
                   "www.github.com/p4vv37/blender_command_port"
                   "www.github.com/jeffhanna/blender_command_port",
    "author": "Pawel Kowalski, Jeff Hannna",
    "version": (1, 2, 2),
    "blender": (2, 93, 0),
    "location": "User preferences > Blender Command Port",
    "support": "COMMUNITY",
    "wiki_url": "www.github.com/p4vv37/blender_command_port",
    "category": "Development",
}

import bpy
from bpy.types import Panel

from .command_port import register as register_command_port
from .command_port import unregister as unregister_command_port
from .command_port import CommandPortOperator


class OpenCommandPortOperator(bpy.types.Operator):
    bl_idname = "wm.open_command_port"
    bl_label = "Open Port"

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def execute(self, context):
        bpy.ops.object.command_port('INVOKE_DEFAULT')
        return {'FINISHED'}


class CloseCommandPortOperator(bpy.types.Operator):
    bl_idname = "wm.close_command_port"
    bl_label = "Close Port"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        try:
            if not CommandPortOperator.instance.is_alive():
                print("Port is not running")
                return False
            CommandPortOperator.instance.do_run = False
            print("Command port closed")
        except NameError:
            print("Port is not running. It was never initialized.")
        return {'FINISHED'}


class BLENDERCOMMANDPORT1_PT_Panel(Panel):
    bl_label = 'Blender Command Port'

    # 2.8 uses PREFERENCES and system. There is no need to attempt to context
    # switch between Blender 2.7 and 2.8 here as the 'blender' version metadata
    # at the top of this file limits it to Blender 2.80 or later.

    bl_space_type = 'PREFERENCES'
    bl_context = 'system'
    bl_region_type = 'WINDOW'

    def draw(self, context):
        layout = self.layout
        window_manager = context.window_manager
        layout.prop(window_manager, 'bcp_queue_size')
        layout.prop(window_manager, 'bcp_timeout')
        layout.prop(window_manager, 'bcp_port')
        layout.prop(window_manager, 'bcp_buffersize')
        layout.prop(window_manager, 'bcp_max_connections')
        layout.prop(window_manager, 'bcp_return_result')
        layout.prop(window_manager, 'bcp_result_as_json')
        layout.prop(window_manager, 'bcp_redirect_output')
        layout.prop(window_manager, 'bcp_share_environ')
        row = layout.row()
        try:
            port_running = CommandPortOperator.instance.is_alive()
        except AttributeError:
            port_running = False

        if port_running:
            row.operator("wm.close_command_port")
        else:
            row.operator("wm.open_command_port")


def register():
    bpy.utils.register_class(OpenCommandPortOperator)
    bpy.utils.register_class(CloseCommandPortOperator)
    register_command_port()
    bpy.utils.register_class(BLENDERCOMMANDPORT1_PT_Panel)


def unregister():
    bpy.utils.unregister_class(OpenCommandPortOperator)
    bpy.utils.unregister_class(CloseCommandPortOperator)
    unregister_command_port()
    bpy.utils.unregister_class(BLENDERCOMMANDPORT1_PT_Panel)

