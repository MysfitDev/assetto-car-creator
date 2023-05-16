bl_info = {
    "name": "Assetto Car Creator",
    "author": "Jesse Myers",
    "description" : "Provides useful tools for creating and editing Assetto Corsa custom cars",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (0, 0, 5, 0)
}

import bpy
import math
import textwrap

from . import (addon_updater_ops,
                ahc_ui,
                ahc_ops)

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
                       
from bpy.types import (AddonPreferences,
                       PropertyGroup,
                       )
                       
from mathutils import Matrix
from mathutils import Vector

class AHC_Addon_Properties(PropertyGroup):
    bl_idname = "object.assetto_hierarchy_props"
    bl_label = "Property Example"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name: StringProperty(
        name="Collection Name",
        description="",
        default="New Car",
        maxlen=24,
        )
    
    wheel_base: FloatProperty(
        name = "Wheel Base (m)",
        description = "",
        default = 2.43,
        precision = 4,
        min = 0.0,
        max = 100.0
        )
     
    front_track_width: FloatProperty(
        name = "Front Track Width (m)",
        description = "",
        default = 0.0,
        precision = 4,
        min = 0.0,
        max = 100.0
        )
     
    rear_track_width: FloatProperty(
        name = "Rear Track Width (m)",
        description = "",
        default = 0.0,
        precision = 4,
        min = 0.0,
        max = 100.0
        )
     
    rim_diameter: IntProperty(
        name = "Rim Diameter (in)",
        description = "",
        default = 0,
        min = 0,
        max = 30
        )
     
    tire_width: IntProperty(
        name = "Tire Width (mm)",
        description = "",
        default = 150,
        min = 150,
        max = 500
        )
     
    tire_aspect: IntProperty(
        name = "Tire Aspect Ratio",
        description = "",
        default = 0,
        min = 0,
        max = 100
        )
     
    root_node: PointerProperty(
        type = bpy.types.Object,
        name = "Object"
        )
     
    node_to_reposition: PointerProperty(
        type = bpy.types.Object,
        name = "Object"
        )
        
    scale_adjust: FloatProperty(
        name = "Scale Multiplier",
        description = "",
        default = 1.0,
        precision = 4,
        min = 0.0001
        )
        
    root_final_scale: FloatProperty(
        name = "Root Final Scale",
        description = "",
        default = 0.01,
        precision = 4,
        min = 0.0001
        )
        
    include_child_translation: BoolProperty(
        name = "Include Child Translation",
        default = True
        )
    
    def execute(self, context):
        self.report({'INFO'}, self.collection_name)
        return {'FINISHED'}

@addon_updater_ops.make_annotations
class AHC_Addon_Preferences(AddonPreferences):
    """Demo bare-bones preferences"""
    bl_idname = __package__

    # Addon updater preferences.

    auto_check_update = bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False)

    updater_interval_months = bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0)

    updater_interval_days = bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
        max=31)

    updater_interval_hours = bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23)

    updater_interval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59)

    def draw(self, context):
        layout = self.layout
        mainrow = layout.row()
        col = mainrow.column()
        addon_updater_ops.update_settings_ui(self, context)
        
classes = (
    AHC_Addon_Preferences,
    AHC_Addon_Properties,
)

def register():
    addon_updater_ops.register(bl_info)
    
    from bpy.utils import register_class
    for cls in classes:
        addon_updater_ops.make_annotations(cls)  # Avoid blender 2.8 warnings.
        register_class(cls)
        
    ahc_ops.register()
    ahc_ui.register(AHC_Addon_Properties.bl_idname)
    
    bpy.types.Scene.ahc_tool = PointerProperty(type=AHC_Addon_Properties)

def unregister():
    # Addon updater unregister.
    addon_updater_ops.unregister()
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls) 
        
    ahc_ops.unregister()
    ahc_ui.unregister()
    
    del bpy.types.Scene.ahc_tool