bl_info = {
    "name": "Assetto Car Creator",
    "author": "Jesse Myers",
    "description" : "Provides useful tools for creating and editing Assetto Corsa custom cars",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (0, 0, 4, 3)
}

import bpy
import math
import textwrap
from . import addon_updater_ops

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
                       
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )
                       
from mathutils import Matrix
from mathutils import Vector

def multiline_label(parent, context, text):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

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

class OBJECT_OT_AssettoMaterialCreation(Operator):
    """Assetto Material Creation"""
    bl_idname = "object.assetto_hierarchy_material_creation"
    bl_label = "Create Base Materials"
    bl_options = {'REGISTER', 'UNDO'}
    
    EXT_MATERIALS = [
        'EXT_Tyre',
        'EXT_Rim',
        'EXT_Carpaint',
        'EXT_Carbon',
        'EXT_Details_AT',
        'EXT_Details_Plastic',
        'EXT_Details_Metal',
        'EXT_Details_Chrome',
        'EXT_Disc',
        'EXT_Caliper',
        'EXT_Window',
        'EXT_Lights_Glass',
        'EXT_Lights_Chrome'
    ]
    
    INT_MATERIALS = [
        'INT_Details_AT',
        'INT_Details_Plastic',
        'INT_Details_Chrome',
        'INT_Details_Metal_Flat',
        'INT_Details_Gauges',
        'INT_LCD',
        'INT_FUEL_INDICATOR',
    ]
    
    def setup_material_list(self, material_list):
        for mat_name in material_list:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            #setup the node_tree and links as you would manually on shader Editor
            #to define an image texture for a material
            material_output = mat.node_tree.nodes.get('Material Output')
            principled_BSDF = mat.node_tree.nodes.get('Principled BSDF')

            tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            mat.node_tree.links.new(tex_node.outputs[0], principled_BSDF.inputs[0])
            bpy.data.materials[mat_name].node_tree.nodes["Principled BSDF"].inputs[0].show_expanded = True
            
            if(mat_name.endswith(("_AT", "_Alpha"))):
                mat.blend_method = 'BLEND'

    def execute(self, context):
        scene = context.scene
        ahc_tool = scene.ahc_tool
                   
        self.setup_material_list(self.EXT_MATERIALS)
        self.setup_material_list(self.INT_MATERIALS)
        
        return {'FINISHED'}

class OBJECT_OT_AssettoMeshRename(Operator):
    """Assetto Mesh Rename"""
    bl_idname = "object.assetto_hierarchy_mesh_renamer"
    bl_label = "Rename Meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        def rename_object(obj):   
            count = 0             
            for child in obj.children:
                if child.type == 'MESH':
                    if child.visible_get():
                        child.name = '{}_SUB{}'.format(child.parent.name, count)
                        count = count + 1
                rename_object(child)
        
        rename_object(ahc_tool.root_node)
        return {'FINISHED'}

class OBJECT_OT_AssettoMaterialImageReload(Operator):
    """Assetto Material Image Reload"""
    bl_idname = "object.assetto_hierarchy_material_image_reloader"
    bl_label = "Reload All Textures From File"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for image in bpy.data.images:
            image.reload()
        return {'FINISHED'}

class OBJECT_OT_AssettoMeshAdjustScale(Operator):
    """Assetto Mesh Scale Adjuster"""
    bl_idname = "object.assetto_hierarchy_mesh_scale_adjuster"
    bl_label = "Adjust Mesh Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        def select_children(obj):
            for child in obj.children:
                child.select_set(True)
                select_children(child)
            
        def scale_object(obj, scale_adjustment):   
            for ob in bpy.context.selected_objects:
                ob.select_set(False)
                
            obj.select_set(True)
            obj.scale *= (scale_adjustment / ahc_tool.root_final_scale)
            select_children(obj)
                
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            
            for ob in bpy.context.selected_objects:
                ob.select_set(False)
                
        scale_object(ahc_tool.root_node, ahc_tool.scale_adjust)
                
        ahc_tool.root_node.select_set(True)
        ahc_tool.root_node.scale *= ahc_tool.root_final_scale
        ahc_tool.root_node.select_set(False)
        
        return {'FINISHED'}

class OBJECT_OT_AssettoHierarchy(Operator):
    """Assetto Hierarchy Creator"""
    bl_idname = "object.create_assetto_hierarchy"
    bl_label = "Create Assetto Hierarchy"
    bl_options = {'REGISTER', 'UNDO'}

    # Makes an empty, at location, stores it in existing collection
    def make_empty(self, context, name, location, coll_name, parent_name = "", type = "PLAIN_AXES", radius=0.01):
        bpy.ops.object.empty_add(type=type, radius=radius, location=location, scale=(1, 1, 1))
        empty_obj = bpy.context.active_object 
        bpy.ops.object.collection_link(collection=coll_name)
        context.scene.collection.objects.unlink(empty_obj)
        empty_obj.name = name
        
        if(parent_name != ""):
            empty_obj.parent = bpy.data.objects[parent_name]
            
        empty_obj.select_set(False)
        return empty_obj

    def execute(self, context):
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        root_empty_name = ahc_tool.collection_name + "_root"
        root_location = (0,0,0)
        
        rim_dia_m = ahc_tool.rim_diameter * 0.0254
        rim_dia_mm = rim_dia_m * 0.01
        tire_width_mm = ahc_tool.tire_width * 0.01
        wheel_base_mm = (ahc_tool.wheel_base / 2) * 0.01
        
        rim_radius_mm = (rim_dia_mm / 2)
        tire_radius_add_mm = (tire_width_mm * (ahc_tool.tire_aspect / 100.0)) * 0.0001
        wheel_radius_mm = rim_radius_mm + tire_radius_add_mm
        
        front_track_width_mm = (ahc_tool.front_track_width / 2) * 0.01
        rear_track_width_mm = (ahc_tool.rear_track_width / 2) * 0.01
        
        lf_wheel_location = (front_track_width_mm, wheel_radius_mm, wheel_base_mm)
        rf_wheel_location = (-1 * front_track_width_mm, wheel_radius_mm, wheel_base_mm)
        lr_wheel_location = (rear_track_width_mm, wheel_radius_mm, -1 * wheel_base_mm)
        rr_wheel_location = (-1 * rear_track_width_mm, wheel_radius_mm, -1 * wheel_base_mm)


        carRootCollection = bpy.data.collections.new(ahc_tool.collection_name)
        bpy.context.scene.collection.children.link(carRootCollection)

        root_empty = self.make_empty(context, root_empty_name, root_location, ahc_tool.collection_name)
        
        bpy.data.objects[root_empty_name].rotation_euler[0] = math.radians(90)
        
        # Make cockpit
        self.make_empty(context, "COCKPIT_HR", root_location, ahc_tool.collection_name, root_empty_name)
        
        # Make wheels
        self.make_empty(context, "WHEEL_LF", lf_wheel_location, ahc_tool.collection_name, root_empty_name, "SPHERE", wheel_radius_mm*1.5)
        self.make_empty(context, "WHEEL_RF", rf_wheel_location, ahc_tool.collection_name, root_empty_name, "SPHERE", wheel_radius_mm*1.5)
        self.make_empty(context, "WHEEL_LR", lr_wheel_location, ahc_tool.collection_name, root_empty_name, "SPHERE", wheel_radius_mm*1.5)
        self.make_empty(context, "WHEEL_RR", rr_wheel_location, ahc_tool.collection_name, root_empty_name, "SPHERE", wheel_radius_mm*1.5)
        
        # Make Suspension
        self.make_empty(context, "SUSP_LF", lf_wheel_location, ahc_tool.collection_name, root_empty_name, radius=0.006)
        self.make_empty(context, "SUSP_RF", rf_wheel_location, ahc_tool.collection_name, root_empty_name, radius=0.006)
        self.make_empty(context, "SUSP_LR", lr_wheel_location, ahc_tool.collection_name, root_empty_name, radius=0.006)
        self.make_empty(context, "SUSP_RR", rr_wheel_location, ahc_tool.collection_name, root_empty_name, radius=0.006)
        
        # Make main body
        self.make_empty(context, "x0_main_body", root_location, ahc_tool.collection_name, root_empty_name)
        
        return {'FINISHED'}

class OBJECT_OT_AssettoMeshEmptyPositioner(Operator):
    """Assetto Mesh Positioner"""
    bl_idname = "object.assetto_hierarchy_mesh_positioner"
    bl_label = "Center to Direct Children"
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_obj_mesh_center(self, obj):
        # Total value of each vertex
        x, y, z = [ sum( [v.co[i] for v in obj.data.vertices] ) for i in range(3)]
        # number of vertices
        count = float(len(obj.data.vertices))
        # Divide the sum of each vector by the number of vertices
        # And make the position a world reference.
        center = (Vector( (x, y, z ) ) / count )        
        self.report({'INFO'}, 'Child Center: {}.'.format(center))
        
        return center

    def execute(self, context):
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        obj= [i.matrix_world.translation for i in ahc_tool.node_to_reposition.children]
        x, y, z = (0, 0, 0)
        
        for child in ahc_tool.node_to_reposition.children:
            if child.type == 'MESH':
                if child.visible_get():
                    child_center = self.get_obj_mesh_center(child)
                    x += child_center[0]
                    y += child_center[1]
                    z += child_center[2]
                    
                    if ahc_tool.include_child_translation:
                        child_translation = child.matrix_world.translation
                        x += child_translation[0]
                        y += child_translation[1]
                        z += child_translation[2]
                        
        l = len(obj)
        global_loc = Vector((x/l,y/l,z/l))
        self.report({'INFO'}, 'Centered {} to median children (count: {}) location.'.format(ahc_tool.node_to_reposition.name, len(ahc_tool.node_to_reposition.children)))
        
        mw = ahc_tool.node_to_reposition.matrix_world 
        target_local_loc = mw.inverted() @ global_loc   
        ahc_tool.node_to_reposition.matrix_world.translation = global_loc

        for child_obj in ahc_tool.node_to_reposition.children:
            child_obj.matrix_parent_inverse.translation -= target_local_loc
            
        return {'FINISHED'}

class OBJECT_PT_AssettoHierarchyPanel(Panel):
    bl_label = 'Assetto Car Hierarchy'
    bl_idname = 'AHC_PT_AssettoHierarchyPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assetto'
    
    def draw(self, context):
        addon_updater_ops.check_for_update_background()
        
        props = self.layout.operator(AHC_Addon_Properties.bl_idname)
        
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
        row.operator(OBJECT_OT_AssettoHierarchy.bl_idname)
        
        addon_updater_ops.update_notice_box_ui(self, context)

class OBJECT_PT_AssettoMaterialPanel(Panel):
    bl_label = 'Assetto Materials'
    bl_idname = 'AHC_PT_AssettoMaterialPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assetto'
    
    def draw(self, context):
        props = self.layout.operator(AHC_Addon_Properties.bl_idname)
        
        layout = self.layout
        scene = context.scene
        ahc_tool = scene.ahc_tool
        
        col = layout.column()
        col.operator(OBJECT_OT_AssettoMaterialCreation.bl_idname)
        col.operator(OBJECT_OT_AssettoMaterialImageReload.bl_idname)
        
class OBJECT_PT_AssettoMeshCleanupPanel(Panel):
    bl_label = 'Assetto Mesh Cleanup'
    bl_idname = 'AHC_PT_AssettoMeshCleanupPanel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Assetto'
    
    def draw(self, context):
        props = self.layout.operator(AHC_Addon_Properties.bl_idname)
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
        row.operator(OBJECT_OT_AssettoMeshRename.bl_idname)
        
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
        row.operator(OBJECT_OT_AssettoMeshAdjustScale.bl_idname)
        
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
        row.operator(OBJECT_OT_AssettoMeshEmptyPositioner.bl_idname)
        
@addon_updater_ops.make_annotations
class AHC_Addon_Preferences(bpy.types.AddonPreferences):
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

        # Works best if a column, or even just self.layout.
        mainrow = layout.row()
        col = mainrow.column()

        # Updater draw function, could also pass in col as third arg.
        addon_updater_ops.update_settings_ui(self, context)

        # Alternate draw function, which is more condensed and can be
        # placed within an existing draw function. Only contains:
        #   1) check for update/update now buttons
        #   2) toggle for auto-check (interval will be equal to what is set above)
        # addon_updater_ops.update_settings_ui_condensed(self, context, col)

        # Adding another column to help show the above condensed ui as one column
        # col = mainrow.column()
        # col.scale_y = 2
        # ops = col.operator("wm.url_open","Open webpage ")
        # ops.url=addon_updater_ops.updater.website
        
classes = (
    AHC_Addon_Preferences,
    AHC_Addon_Properties,
    OBJECT_OT_AssettoMaterialCreation,
    OBJECT_OT_AssettoMaterialImageReload,
    OBJECT_OT_AssettoMeshRename,
    OBJECT_OT_AssettoMeshAdjustScale,
    OBJECT_OT_AssettoHierarchy,
    OBJECT_OT_AssettoMeshEmptyPositioner,
    OBJECT_PT_AssettoHierarchyPanel,
    OBJECT_PT_AssettoMaterialPanel,
    OBJECT_PT_AssettoMeshCleanupPanel,
)

def register():
    addon_updater_ops.register(bl_info)
    
    from bpy.utils import register_class
    for cls in classes:
        addon_updater_ops.make_annotations(cls)  # Avoid blender 2.8 warnings.
        register_class(cls)
    
    bpy.types.Scene.ahc_tool = PointerProperty(type=AHC_Addon_Properties)

def unregister():
    # Addon updater unregister.
    addon_updater_ops.unregister()
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls) 
    
    del bpy.types.Scene.ahc_tool
    
if __name__ == '__main__':
    register()