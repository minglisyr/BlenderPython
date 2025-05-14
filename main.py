import bpy
import math
import os
from mathutils import Vector
import time

start_time = time.time()

### Geometry Input
# Belt/Tooth
Tooth_Number = 220
Belt_Width = 11

# Sprockets
Diameter_Large = 300
Diameter_Small = 150

### Auto Clean Up ***
# Select all objects
bpy.ops.object.select_all(action='SELECT')

# Delete all selected objects
bpy.ops.object.delete(use_global=False)

# Purge orphaned data (run multiple times to ensure all orphans are removed)
for _ in range(3):
    bpy.ops.outliner.orphans_purge()

### Importing 2D Profile ***

# Use os.path for cross-platform compatibility
profile_path = os.path.join("C:/", "Users", "ml2954", "Documents", "BlenderPython", "Profile.obj")
bpy.ops.wm.obj_import(filepath=profile_path)

# Replace 'Curve' with the name of your imported 2D object
obj_name = "Profile\Surface"  # Fixed backslash issue
extrude_thickness = Belt_Width  # Set your desired thickness here

# Get the object safely
obj = bpy.data.objects.get(obj_name)
if not obj:
    raise ValueError(f"Object '{obj_name}' not found. Check the imported file and object name.")

### Math preparation
bbox = obj.bound_box
tooth_length = bbox[4][0] - bbox[0][0] # Length of Tooth
belt_length = tooth_length * Tooth_Number

def calculate_center_distance(L, D1, D2):
    term1 = (L - (math.pi / 2) * (D1 + D2)) / 4
    term2 = math.sqrt(term1**2 - ((D1 - D2) / 2)**2)
    return term1 + term2

tooth_number_large = round(math.pi * Diameter_Large / tooth_length)
tooth_number_small = round(math.pi * Diameter_Small / tooth_length)

center_distance = calculate_center_distance(belt_length, Diameter_Large, Diameter_Small)
print(f"Center distance: {center_distance:.2f} mm")
print(f"Belt length: {belt_length:.2f} mm")
print(f"Sprocket Large: Dia. = {Diameter_Large:.2f} mm, Tooth# = {tooth_number_large}")
print(f"Sprocket Small: Dia. = {Diameter_Small:.2f} mm, Tooth# = {tooth_number_small}")

# Ensure the object is selected and active
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

### Extruding 2D Profile into 3D Unit ***

# If it's a curve, set extrusion
if obj.type == 'CURVE':
    obj.data.extrude = extrude_thickness
    # Optionally, convert to mesh if you need mesh geometry
    bpy.ops.object.convert(target='MESH')

# If it's already a mesh, use mesh extrusion
elif obj.type == 'MESH':
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # Extrude along Y axis
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, extrude_thickness, 0)}
    )
    bpy.ops.object.mode_set(mode='OBJECT')
else:
    raise TypeError(f"Unsupported object type: {obj.type}. Only 'CURVE' and 'MESH' are supported.")

# Flip the 3D Unit around
obj.rotation_mode = 'XYZ'  
obj.rotation_euler[1] = math.pi

####################################################################################
# === CALCULATE POSITIONS ===
R1 = Diameter_Large / 2
R2 = Diameter_Small / 2
CD = center_distance

# Sprocket centers (X-Z plane)
O1 = Vector((0, 0, 0))
O2 = Vector((CD, 0, 0))

# Angle from O1 to O2 (in X-Z)
phi = math.atan2(O2.z - O1.z, O2.x - O1.x)

# Angle to tangent points
theta = math.acos((R1 - R2) / CD)

# Tangent point directions (upper and lower)
angle_upper = phi + theta
angle_lower = phi - theta

# Upper tangent points (X-Z plane)
P1u = O1 + Vector((R1 * math.cos(angle_upper), 0, R1 * math.sin(angle_upper)))
P2u = O2 + Vector((R2 * math.cos(angle_upper), 0, R2 * math.sin(angle_upper)))

# Lower tangent points (X-Z plane)
P1l = O1 + Vector((R1 * math.cos(angle_lower), 0, R1 * math.sin(angle_lower)))
P2l = O2 + Vector((R2 * math.cos(angle_lower), 0, R2 * math.sin(angle_lower)))

# === CREATE CURVE DATA ===

def arc_points(center, radius, start, end, segments=64):
    # Compute start and end angles
    a1 = math.atan2(start.z - center.z, start.x - center.x)
    a2 = math.atan2(end.z - center.z, end.x - center.x)
    # Ensure arc goes counterclockwise
    if a2 < a1:
        a2 += 2 * math.pi
    return [
        center + Vector((
            radius * math.cos(a1 + t * (a2 - a1) / segments),
            0,
            radius * math.sin(a1 + t * (a2 - a1) / segments)))
        for t in range(segments + 1)
    ]

# Build the curve points: arc1 -> tangent1 -> arc2 -> tangent2
arc1 = arc_points(O1, R1, P1u, P1l)
arc2 = arc_points(O2, R2, P2l, P2u)

curve_points = []
curve_points.extend(arc1)
curve_points.append(P2l)
curve_points.extend(arc2)
curve_points.append(P1u)

# === CREATE BLENDER CURVE OBJECT ===
curve_data = bpy.data.curves.new('BeltCurve', type='CURVE')
curve_data.dimensions = '3D'
curve_data.resolution_u = 2

polyline = curve_data.splines.new('POLY')
polyline.points.add(len(curve_points) - 1)
for i, pt in enumerate(curve_points):
    polyline.points[i].co = (pt.x, pt.y, pt.z, 1)

polyline.use_cyclic_u = True  # Close the loop

curve_obj = bpy.data.objects.new('BeltCurve', curve_data)
bpy.context.collection.objects.link(curve_obj)

# OPTIONAL: Select and focus
bpy.context.view_layer.objects.active = curve_obj
curve_obj.select_set(True)

###########################################################################
# Ensure the object is selected and active
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.modifier_add(type='ARRAY')
bpy.context.object.modifiers["Array"].fit_type = 'FIT_CURVE'
bpy.context.object.modifiers["Array"].curve = bpy.data.objects["BeltCurve"]

bpy.ops.object.modifier_add(type='CURVE')
bpy.context.object.modifiers["Curve"].object = bpy.data.objects["BeltCurve"]

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 720

#### Setup animation for belt moving
obj = bpy.context.object
# Set and keyframe initial location at frame 1
bpy.context.scene.frame_set(1)
obj.location[0] = 0
obj.keyframe_insert(data_path="location", index=0)

# Set and keyframe final location at frame 720
bpy.context.scene.frame_set(720)
obj.location[0] = - math.pi * Diameter_Large * 2
obj.keyframe_insert(data_path="location", index=0)

# Set interpolation to LINEAR for the rotation channel
action = obj.animation_data.action
for fcurve in action.fcurves:
    if fcurve.data_path == "location" and fcurve.array_index == 0:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'

##### Create Sprockets
offset_large = 5
offset_small = 4

# Create the large gear
bpy.ops.mesh.primitive_gear(align='WORLD', location=(0, - Belt_Width / 4, 0), rotation=(math.pi / 2, 0, 0), change=False)
bpy.ops.mesh.primitive_gear(change=True, number_of_teeth=tooth_number_large, radius=Diameter_Large / 2 - offset_large, 
                            addendum=4, dedendum=0, angle=0.3, base=3, width=Belt_Width/2, skew=0, conangle=0, crown=0.5)

bpy.context.object.rotation_euler[1] = math.radians(2)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

obj = bpy.context.object
# Set and keyframe initial rotation at frame 1
bpy.context.scene.frame_set(1)
obj.rotation_euler[1] = 0
obj.keyframe_insert(data_path="rotation_euler", index=1)

# Set and keyframe final rotation at frame 720
bpy.context.scene.frame_set(720)
obj.rotation_euler[1] = 12.5664
obj.keyframe_insert(data_path="rotation_euler", index=1)

# Set interpolation to LINEAR for the rotation channel
action = obj.animation_data.action
for fcurve in action.fcurves:
    if fcurve.data_path == "rotation_euler" and fcurve.array_index == 1:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'

# Rename the active object to GearLarge
bpy.context.active_object.name = "GearLarge"

# Create the small gear
bpy.ops.mesh.primitive_gear(align='WORLD', location=(CD, - Belt_Width / 4, 0), rotation=(math.pi / 2, 0, 0), change=False)
bpy.ops.mesh.primitive_gear(change=True, number_of_teeth=tooth_number_small, radius=Diameter_Small / 2 - offset_small, 
                            addendum=4, dedendum=0, angle=0.3, base=3, width=Belt_Width/2, skew=0, conangle=0, crown=0.5)

bpy.context.object.rotation_euler[1] = math.radians(6)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

obj = bpy.context.object
# Set and keyframe initial rotation at frame 1
bpy.context.scene.frame_set(1)
obj.rotation_euler[1] = 0
obj.keyframe_insert(data_path="rotation_euler", index=1)

# Set and keyframe final rotation at frame 720
bpy.context.scene.frame_set(720)
obj.rotation_euler[1] = 12.5664 * (Diameter_Large / Diameter_Small)
obj.keyframe_insert(data_path="rotation_euler", index=1)

# Set interpolation to LINEAR for the rotation channel
action = obj.animation_data.action
for fcurve in action.fcurves:
    if fcurve.data_path == "rotation_euler" and fcurve.array_index == 1:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'
            
# Rename the active object to GearSmall
bpy.context.active_object.name = "GearSmall"

################ Color assigning
# Get the objects by name (ensure names are correct)
obj_belt = bpy.data.objects['Profile\\Surface']  # Use double backslash if the name contains a backslash
obj_gl = bpy.data.objects['GearLarge']
obj_gs = bpy.data.objects['GearSmall']

# Create Red material
matRed = bpy.data.materials.new(name="RedMaterial")
matRed.use_nodes = True
bsdf_red = matRed.node_tree.nodes["Principled BSDF"]
bsdf_red.inputs['Base Color'].default_value = (1, 0, 0, 1)  # Red

# Create Blue material
matBlue = bpy.data.materials.new(name="BlueMaterial")
matBlue.use_nodes = True
bsdf_blue = matBlue.node_tree.nodes["Principled BSDF"]
bsdf_blue.inputs['Base Color'].default_value = (0, 0, 1, 1)  # Blue

# Create Green material
matGreen = bpy.data.materials.new(name="GreenMaterial")
matGreen.use_nodes = True
bsdf_green = matGreen.node_tree.nodes["Principled BSDF"]
bsdf_green.inputs['Base Color'].default_value = (0, 1, 0, 1)  # Green

# Assign materials to objects
def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

assign_material(obj_belt, matRed)
assign_material(obj_gl, matBlue)
assign_material(obj_gs, matGreen)

################### Animation Setup

time_elapsed = (time.time() - start_time) * 1000
print(f"Time elapsed = {time_elapsed:.2f} ms")                            
