bl_info = {
    "name": "Target Weld Tool",
    "description":"Drag a vertex to merge it to the second vertex",
    "author": "Justin Graham",
    "location": "View3D > Vertex",
    "blender": (2,80,0),
    "category": "Mesh"
}
import bpy
import bmesh
import mathutils
import blf
import gpu
import bpy_extras
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader

class TargetWeldTool(bpy.types.Operator):
    bl_idname = "mesh.target_weld"
    bl_label = "Target Weld"
    bl_options = {'REGISTER', 'UNDO'}


    def modal(self,context: bpy.types.Context, event: bpy.types.Event):
        if event.type == 'MOUSEMOVE':
            self.mouse_x = event.mouse_x
            self.mouse_y = event.mouse_y

            if self.drawing:
                context.area.tag_redraw()
                #self.draw_callback_px(context)

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            #Drawing
            self.drawing = True

            #Selects Source Vert for operation
            selectedVerts = None
            bpy.ops.view3d.select(deselect_all=True)
            self.loc = [event.mouse_region_x, event.mouse_region_y]
            bpy.ops.view3d.select(location=self.loc, extend=False)

            #Save Mode and swap to object mode to update the selection
            mode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode='OBJECT')
            selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]
            self.source_vertex = selectedVerts

            #Revert back to previous mode
            bpy.ops.object.mode_set(mode=mode)    

            #Checks if valid vertex is selected and stores the vert
            if len(self.source_vertex) > 0:
                if isinstance(self.source_vertex[0], bpy.types.MeshVertex):
                    print ("Source Vert Found")
                    self.vert1 = self.source_vertex[0].index
                else:
                    self.drawing = False
                    self.report({'WARNING'}, "Must Select a Vertice")

            else:
                self.drawing = False
                self.report({'WARNING'}, "Must Select a Vertice")

        elif event.type =='LEFTMOUSE' and event.value =='RELEASE':
            # Remove the Drawing Line
            self.drawing = False

            #Selects the Target Vert for operation
            selectedVerts = None
            bpy.ops.view3d.select(deselect_all=True)
            self.loc = [event.mouse_region_x, event.mouse_region_y]
            bpy.ops.view3d.select(location=self.loc, extend=False)

            #Assigns Target Vert
            mode = bpy.context.active_object.mode
            bpy.ops.object.mode_set(mode='OBJECT')
            selectedVerts = [v for v in bpy.context.active_object.data.vertices if v.select]
            self.target_vertex = selectedVerts
            
            #Revert back to previous mode
            bpy.ops.object.mode_set(mode=mode)

            #Checks if valid vertex is selected, stores the vert, and calls target_weld passing in the first and second vert
            if len(self.target_vertex) > 0:
                if isinstance(self.target_vertex[0], bpy.types.MeshVertex):
                    print ("Target Vert Found")
                    self.vert2 = self.target_vertex[0].index
                    self.target_weld(context,self.vert1,self.vert2)
                    return{'RUNNING_MODAL'}
                else:
                    self.report({'WARNING'}, "Must Select a Vertice")
            else:
                self.report({'WARNING'}, "Must Select a Vertice")

        elif event.type in {'ESC', 'RIGHTMOUSE'}:
            #Cancel Target Weld
            self.is_dragging= False
            #Remove Draw Handler
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW') 
            bpy.types.SpaceView3D.draw_handler_remove(self.UI_handler,'WINDOW')
            bpy.context.window.cursor_modal_restore()
            context.area.tag_redraw()
            return {'FINISHED'}
        return {'RUNNING_MODAL'}
    
    def get_mouse_position(self):
        
        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d
        mouse_pos = [self.mouse_x, self.mouse_y]

        view_vector = view3d_utils.region_2d_to_vector_3d(region, region_3d, mouse_pos)
        self.loc = view3d_utils.region_2d_to_location_3d(region, region_3d, mouse_pos, view_vector)
        #view_vector = (0,0,0)
        return self.loc
    
    def draw_callback_px(self):
        if self.drawing and len(self.source_vertex) > 0:
            # Get the 3D coordinates of the selected vertex
            scene = bpy.context.scene
            mpos = self.get_mouse_position()
            mpos = (mpos.x,mpos.y,mpos.z - .5)
            source_coords = self.source_vertex[0].co
            coords = [source_coords, mpos]

            #self.shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            self.batch = batch_for_shader(self.shader, 'LINES', {"pos": coords})

            self.batch.draw(self.shader)

    #Create UI
    def draw_UI(tmp,self,context):
        region = context.region
        font_id = 0
        font_size = 30

        xt = int(region.width / 2.0)
        yt = 50
        text = "Drag One Vertex Onto Another"
        
        blf.size(font_id,font_size, 72)
        blf.position(font_id, xt - blf.dimensions(font_id,text)[0] / 2, yt, 0)
        blf.color(font_id,1.0,1.0,1.0,1.0)

        blf.draw(font_id,text)

    def invoke(self,context,event):
        if context.object and context.object.type == 'MESH':

            #Initialize Lines
            self.shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            self.shader.uniform_float("color", (1,1,0,1))

            bpy.context.window.cursor_modal_set('CROSSHAIR')

            if bpy.context.mode != 'EDIT_MESH' and bpy.context.tool_settings.mesh_select_mode[0]:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='VERT')

            #Initialize Variables
            self.is_dragging = True
            self.mouse_x = event.mouse_x
            self.mouse_y = event.mouse_y
            self.source_vertex = None
            self.target_vertex = None
            self.drawing = False

            args = (self, context)

            # Create the Draw Handler
            self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (), 'WINDOW', 'POST_VIEW')

            #Create UI Handler
            self.UI_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_UI, (args), 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            context.area.tag_redraw()
            return {'RUNNING_MODAL'}
        else:
            self.drawing = False
            self.report({'WARNING'}, "Please select a mesh object")
            return {'CANCELLED'}

    #Takes in the first and second vert and merges the first vert into the second vert
    def target_weld(self,context,v1,v2):
        #Create Bmesh for Modification
        obj = bpy.context.active_object
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        #Fixes Finding Verts
        bm.verts.ensure_lookup_table()

        #Merge Operation
        verts = [bm.verts[v1],bm.verts[v2]]
        destination = bm.verts[v2].co
        if verts[0] == verts[1]:
            self.drawing = False
            self.report({'WARNING'}, "Must Select 2 Different Vertices")
            return {'CANCELLED'}
        bmesh.ops.pointmerge(bm,verts=verts,merge_co=destination)
        
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        bm.to_mesh(mesh)
        bm.free()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        bpy.ops.object.mode_set(mode=mode)

        self.drawing = False

def menu_func(self,context):
    self.layout.operator(TargetWeldTool.bl_idname)

def register():
    bpy.utils.register_class(TargetWeldTool)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)

def unregister():
    bpy.utils.unregister_class(TargetWeldTool)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)

if __name__ == "__main__":
    register()
    