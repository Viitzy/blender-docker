import bpy
import csv
import os
import sys
import argparse
import logging
import numpy as np
from scipy.spatial import Delaunay

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def create_terrain_from_csv(csv_path):
    """Create a terrain mesh from CSV data."""
    # Create a new mesh and object
    mesh = bpy.data.meshes.new("terrain")
    obj = bpy.data.objects.new("Terrain", mesh)

    # Link object to scene
    bpy.context.scene.collection.objects.link(obj)

    # Read CSV data
    points = []
    colors = []

    with open(csv_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Get coordinates
            x = float(row["x"])
            y = float(row["y"])
            z = float(row["z"])
            points.append([x, y, z])

            # Get colors
            r = float(row["r"]) / 255.0
            g = float(row["g"]) / 255.0
            b = float(row["b"]) / 255.0
            colors.append((r, g, b, 1.0))

    points = np.array(points)

    # Create triangulation in 2D (using x,y coordinates)
    tri = Delaunay(points[:, :2])

    # Create vertices and faces for the mesh
    vertices = points.tolist()
    faces = tri.simplices.tolist()

    # Create the mesh
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Add vertex colors
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()

    color_layer = mesh.vertex_colors.active

    # Apply colors to faces
    for poly in mesh.polygons:
        for idx, vert_idx in enumerate(poly.vertices):
            color_layer.data[poly.loop_indices[idx]].color = colors[vert_idx]

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    # Add material
    mat = bpy.data.materials.new(name="TerrainMaterial")
    mat.use_nodes = True
    mat.use_backface_culling = True

    # Set up material to use vertex colors
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    nodes.clear()

    # Create nodes
    vertex_color = nodes.new("ShaderNodeVertexColor")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    output = nodes.new("ShaderNodeOutputMaterial")

    # Link nodes
    links.new(vertex_color.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    # Set material properties
    bsdf.inputs["Roughness"].default_value = 0.8
    bsdf.inputs["Specular"].default_value = 0.1

    # Assign material to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj


def export_to_glb(output_path):
    """Export the scene to GLB format."""
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        export_format="GLB",
        use_selection=False,
        export_materials=True,
        export_colors=True,
    )


if __name__ == "__main__":
    # Get arguments passed after "--"
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :]

    parser = argparse.ArgumentParser(
        description="Convert CSV terrain data to GLB."
    )
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", required=True, help="Output GLB file path")
    args = parser.parse_args(argv)

    # Clear existing mesh objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Create terrain from CSV
    log.info(f"Creating terrain from {args.input}")
    terrain = create_terrain_from_csv(args.input)

    # Export to GLB
    log.info(f"Exporting to {args.output}")
    export_to_glb(args.output)
    log.info("Export completed successfully")
