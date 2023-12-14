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

class TargetWeldTool(bpy.types.Operator):
    bl_idname = "mesh.target_weld"
    bl_label = "Target Weld"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self,context: bpy.types.Context, event: bpy.types.Event):

        #if event.type == 'MOUSEMOVE':
        #    self.mouse_x = event.mouse_x
        #    self.mouse_y = event.mouse_y

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            
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
                    self.report({'WARNING'}, "Must Select a Vertice")
            else:
                self.report({'WARNING'}, "Must Select a Vertice")

        elif event.type =='LEFTMOUSE' and event.value =='RELEASE':

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
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    

    def invoke(self,context,event):
        if context.object and context.object.type == 'MESH':

            if bpy.context.mode != 'EDIT_MESH' and bpy.context.tool_settings.mesh_select_mode[0]:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='VERT')

            #Initialize Variables
            self.is_dragging = True
            self.mouse_x = event.mouse_x
            self.mouse_y = event.mouse_y
            self.source_vertex = None
            self.target_vertex = None

            #Add a drawing handler for the line
            #self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            #    self.draw_callback, (context,), 'WINDOW', 'POST_PIXEL'
            #)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
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
        bmesh.ops.pointmerge(bm,verts=verts,merge_co=destination)
        
        mode = bpy.context.active_object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        bm.to_mesh(mesh)
        bm.free()
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        bpy.ops.object.mode_set(mode=mode)


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
    