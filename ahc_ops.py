
import bpy
import math
import textwrap
from . import addon_updater_ops
from . import ahc_ops
                             
from mathutils import (Matrix,
                        Vector,
                        )
                       
from bpy.types import (Operator,
                        )



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
        
        if(bpy.data.materials[mat_name] == None):
            gl_mat = bpy.data.materials.new(name="GL")
            gl_mat.use_nodes = True
        
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


classes = (
    OBJECT_OT_AssettoMaterialCreation,
    OBJECT_OT_AssettoMaterialImageReload,
    OBJECT_OT_AssettoMeshRename,
    OBJECT_OT_AssettoMeshAdjustScale,
    OBJECT_OT_AssettoHierarchy,
    OBJECT_OT_AssettoMeshEmptyPositioner,
)

def register():    
    from bpy.utils import register_class
    for cls in classes:
        addon_updater_ops.make_annotations(cls)  # Avoid blender 2.8 warnings.
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)