bl_info = {
    "name": "Blender Command Port",
    "description": "Command Port implementation for blender. "
                   "www.github.com/p4vv37/blender_command_port"
                   "www.github.com/jeffhanna/blender_command_port",
    "author": "Pawel Kowalski",
    "author": "Jeff Hanna"
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "User preferences > Blender Command Port",
    "support": "COMMUNITY",
    "wiki_url": "www.github.com/p4vv37/blender_command_port",
    "category": "Development",
}

import bpy
from bpy.types import Panel

from .command_port import register as register_command_port
from .command_port import unregister as unregister_command_port
from .command_port import open_command_port
from .tools import close_command_port


class OpenCommandPortOperator(bpy.types.Operator):
    bl_idname = "wm.open_command_port"
    bl_label = "Open Port"

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def execute(self, context):
        open_command_port()
        return {'FINISHED'}


class CloseCommandPortOperator(bpy.types.Operator):
    bl_idname = "wm.close_command_port"
    bl_label = "Close Port"

    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        close_command_port()
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
        scene = context.scene
        layout.prop(scene, 'bcp_queue_size')
        layout.prop(scene, 'bcp_timeout')
        layout.prop(scene, 'bcp_port')
        layout.prop(scene, 'bcp_buffersize')
        layout.prop(scene, 'bcp_max_connections')
        layout.prop(scene, 'bcp_return_result')
        layout.prop(scene, 'bcp_result_as_json')
        layout.prop(scene, 'bcp_redirect_output')
        layout.prop(scene, 'bcp_share_environ')
        row = layout.row()
        try:
            port_running = bpy.context.window_manager.keep_command_port_running
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

