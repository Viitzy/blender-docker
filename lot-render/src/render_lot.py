import bpy
import sys
import pandas as pd
import numpy as np
from pathlib import Path


def clear_scene():
    """Clear existing mesh objects from the scene"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def create_terrain_mesh(vertices, faces):
    """Create a new mesh from vertices and faces"""
    mesh = bpy.data.meshes.new("terrain")
    obj = bpy.data.objects.new("terrain", mesh)

    # Link object to scene
    bpy.context.scene.collection.objects.link(obj)

    # Create mesh from vertices and faces
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    return obj


def process_csv(csv_path):
    """Process CSV file and return vertices and faces"""
    # Read CSV file
    df = pd.read_csv(csv_path)

    # Extract coordinates
    x_coords = df["x"].values
    y_coords = df["y"].values
    z_coords = df["z"].values if "z" in df.columns else np.zeros_like(x_coords)

    # Create vertices
    vertices = list(zip(x_coords, y_coords, z_coords))

    # Create faces (triangles)
    # This is a simple triangulation - you might want to use a more sophisticated method
    faces = []
    n = int(np.sqrt(len(vertices)))
    for i in range(n - 1):
        for j in range(n - 1):
            idx = i * n + j
            faces.append([idx, idx + 1, idx + n])
            faces.append([idx + 1, idx + n + 1, idx + n])

    return vertices, faces


def export_glb(output_path):
    """Export the scene to GLB format"""
    bpy.ops.export_scene.gltf(
        filepath=str(output_path), export_format="GLB", use_selection=False
    )


def main():
    # Get command line arguments
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        print(
            "Usage: blender --background --python render_lot.py -- input.csv output.glb"
        )
        sys.exit(1)

    csv_path, output_path = args

    # Clear existing scene
    clear_scene()

    # Process CSV and create terrain
    vertices, faces = process_csv(csv_path)
    terrain_obj = create_terrain_mesh(vertices, faces)

    # Add a light
    light_data = bpy.data.lights.new(name="light", type="SUN")
    light = bpy.data.objects.new(name="light", object_data=light_data)
    bpy.context.scene.collection.objects.link(light)
    light.location = (5, 5, 10)

    # Add a camera
    cam_data = bpy.data.cameras.new(name="camera")
    cam = bpy.data.objects.new(name="camera", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (10, -10, 10)
    cam.rotation_euler = (0.9, 0, 0.8)

    # Export to GLB
    export_glb(output_path)


if __name__ == "__main__":
    main()
