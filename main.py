import bpy
import math
import os

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
extrude_thickness = 10.0  # Set your desired thickness here

# Get the object safely
obj = bpy.data.objects.get(obj_name)
if not obj:
    raise ValueError(f"Object '{obj_name}' not found. Check the imported file and object name.")

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

### Duplicate 3D Unit & Joining to a loop belt ***

# Parameters
original_obj_name = obj_name  # Replace with your object's name
num_duplicates = 50        # Total number of objects (including original)

# Get the original object safely
original_obj = bpy.data.objects.get(original_obj_name)
if not original_obj:
    raise ValueError(f"Object '{original_obj_name}' not found. Check the object name.")

# Calculate x length (bounding box in local space)
bbox = original_obj.bound_box
x_length = bbox[4][0] - bbox[0][0]

# Calculate total arc length and radius
total_length = x_length * num_duplicates
radius = total_length / (2 * math.pi)
angle_step = 2 * math.pi / num_duplicates

# Deselect all
bpy.ops.object.select_all(action='DESELECT')

# List to keep track of all objects to join
objs_to_join = []

for i in range(num_duplicates):
    # Duplicate the object
    if i == 0:
        new_obj = original_obj
    else:
        # Use bpy.data.objects.new for better performance
        new_obj = original_obj.copy()
        new_obj.data = original_obj.data.copy()
        bpy.context.collection.objects.link(new_obj)
    # Calculate angle
    angle = i * angle_step
    # Set position on X-Z plane (Y is constant)
    new_obj.location = (
        math.cos(angle) * radius,
        original_obj.location.y,  # Y stays constant
        math.sin(angle) * radius
    )
    # Align object tangent to circle (rotate around Y-axis)
    new_obj.rotation_euler[1] = math.pi / 2
    new_obj.rotation_euler[0] = -angle
    new_obj.rotation_euler[1] = -angle  # Negative to align tangent; adjust as needed for your object orientation
   
    objs_to_join.append(new_obj)
    new_obj.select_set(True)

# Set active object for joining
bpy.context.view_layer.objects.active = objs_to_join[0]

# Join all objects into one mesh
bpy.ops.object.join()