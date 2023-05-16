import math
import textwrap

from . import (addon_updater_ops,
                ahc_ops)
                       
from bpy.types import (Panel,
                        Menu,
                        Operator,
                        PropertyGroup,
                        )
                       
from mathutils import (Matrix,
                        Vector,
                        )

properties_bl_idname = "object.assetto_hierarchy_props"

def multiline_label(parent, context, text):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

class OBJECT_PT_AssettoHierarchyPanel(Panel):
    bl_label = 'Assetto Car Hierarchy'
    bl_idname = 'AHC_PT_AssettoHierarchyPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assetto'
    
    def draw(self, context):
        addon_updater_ops.check_for_update_background()
        addon_updater_ops.update_notice_box_ui(self, context)
        
        props = self.layout.operator(properties_bl_idname)
        
        layout = self.layout
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        col = layout.column()
        
        col.prop(ahc_tool, "collection_name")
        
        box = layout.box()
        col = box.column()
        col.label(text = 'Overall Dimensions')
        col.prop(ahc_tool, "wheel_base")
        col.prop(ahc_tool, "front_track_width")
        col.prop(ahc_tool, "rear_track_width")
        
        box = layout.box()
        col = box.column()
        col.label(text = 'Wheel Dimensions')
        col.prop(ahc_tool, "tire_width")
        col.prop(ahc_tool, "tire_aspect")
        col.prop(ahc_tool, "rim_diameter")
                
        row = layout.row()
        if(ahc_tool.collection_name == ""):
            row.enabled = False
        row.operator(ahc_ops.OBJECT_OT_AssettoHierarchy.bl_idname)

class OBJECT_PT_AssettoMaterialPanel(Panel):
    bl_label = 'Assetto Materials'
    bl_idname = 'AHC_PT_AssettoMaterialPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assetto'
    
    def draw(self, context):
        props = self.layout.operator(properties_bl_idname)
        
        layout = self.layout
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        col = layout.column()
        col.operator(ahc_ops.OBJECT_OT_AssettoMaterialCreation.bl_idname)
        col.operator(ahc_ops.OBJECT_OT_AssettoMaterialImageReload.bl_idname)
        
class OBJECT_PT_AssettoMeshCleanupPanel(Panel):
    bl_label = 'Assetto Mesh Cleanup'
    bl_idname = 'AHC_PT_AssettoMeshCleanupPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assetto'
    
    def draw(self, context):
        props = self.layout.operator(properties_bl_idname)
        wrapp = textwrap.TextWrapper(width=50) #50 = maximum length 
        
        layout = self.layout
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        box = layout.box()
        col = box.column()
        col.label(text = 'Mesh Renaming')
        col.prop(ahc_tool, "root_node")
        col.separator()
        if(ahc_tool.root_node != None):
            multiline_label(col, context, text = 'Renames children of {} to {}_SUB#'.format(ahc_tool.root_node.name, ahc_tool.root_node.name))
        
        row = col.row()
        if(ahc_tool.root_node == None):
            row.enabled = False
        row.operator(ahc_ops.OBJECT_OT_AssettoMeshRename.bl_idname)
        
        box = layout.box()
        col = box.column()
        col.label(text = 'Mesh Scale Correction')
        col.prop(ahc_tool, "root_node")
        col.prop(ahc_tool, "scale_adjust")
        col.prop(ahc_tool, "root_final_scale")
        col.separator()
        if(ahc_tool.root_node != None):
            multiline_label(col, context, text = 'Set scale {} to {:.4f} and all nested children to 1'.format(ahc_tool.root_node.name, ahc_tool.root_final_scale))
        
        row = col.row()
        if(ahc_tool.root_node == None):
            row.enabled = False
        row.operator(ahc_ops.OBJECT_OT_AssettoMeshAdjustScale.bl_idname)
        
        box = layout.box()
        col = box.column()
        col.label(text = 'Reposition Meshes')
        col.prop(ahc_tool, "node_to_reposition")
        col.separator()
        if(ahc_tool.include_child_translation == True):
            multiline_label(col, context, text = 'Children origin\'s translation and the children\'s mesh position will be used to calculate the final parent position.')
        else:
            multiline_label(col, context, text = 'Only the children\'s mesh position will be used to calculate the final parent position.')
             
        col.prop(ahc_tool, "include_child_translation")        
        
        row = col.row()
        if(ahc_tool.node_to_reposition == None):
            row.enabled = False
        row.operator(ahc_ops.OBJECT_OT_AssettoMeshEmptyPositioner.bl_idname)

classes = (
    OBJECT_PT_AssettoHierarchyPanel,
    OBJECT_PT_AssettoMaterialPanel,
    OBJECT_PT_AssettoMeshCleanupPanel,
)

def register(properties_bl_idname):
    properties_bl_idname = properties_bl_idname
    
    from bpy.utils import register_class
    for cls in classes:
        addon_updater_ops.make_annotations(cls)  # Avoid blender 2.8 warnings.
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    properties_bl_idname = None