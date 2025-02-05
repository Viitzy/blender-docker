import bpy
import csv
import os
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def create_point_cloud_from_csv(csv_path):
    """Create a point cloud mesh from CSV data."""
    # Create a new mesh and object
    mesh = bpy.data.meshes.new("point_cloud")
    obj = bpy.data.objects.new("PointCloud", mesh)

    # Link object to scene
    bpy.context.scene.collection.objects.link(obj)

    # Read CSV data
    vertices = []
    colors = []

    with open(csv_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Get vertex coordinates
            x = float(row["x"])
            y = float(row["y"])
            z = float(row["z"])
            vertices.append((x, y, z))

            # Get vertex colors
            r = float(row["r"]) / 255.0
            g = float(row["g"]) / 255.0
            b = float(row["b"]) / 255.0
            colors.append((r, g, b, 1.0))

    # Create small faces for each point to make them visible
    faces = []
    point_size = 0.1  # Size of the square for each point

    new_vertices = []
    new_faces = []
    vertex_colors = []

    for i, (x, y, z) in enumerate(vertices):
        # Create a small square for each point
        idx = i * 4
        new_vertices.extend(
            [
                (x - point_size, y - point_size, z),
                (x + point_size, y - point_size, z),
                (x + point_size, y + point_size, z),
                (x - point_size, y + point_size, z),
            ]
        )
        new_faces.append((idx, idx + 1, idx + 2, idx + 3))
        # Repeat the color for each vertex of the square
        vertex_colors.extend([colors[i]] * 4)

    # Create mesh from vertices and faces
    mesh.from_pydata(new_vertices, [], new_faces)
    mesh.update()

    # Add vertex colors
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()

    color_layer = mesh.vertex_colors.active
    for i, color in enumerate(vertex_colors):
        color_layer.data[i].color = color

    # Set object display properties for better visualization
    obj.display_type = "SOLID"

    # Add material for vertex colors
    mat = bpy.data.materials.new(name="PointCloudMaterial")
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
        description="Convert CSV point cloud data to GLB."
    )
    parser.add_argument("--input", required=True, help="Input CSV file path")
    parser.add_argument("--output", required=True, help="Output GLB file path")
    args = parser.parse_args(argv)

    # Clear existing mesh objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Create point cloud from CSV
    log.info(f"Creating point cloud from {args.input}")
    point_cloud = create_point_cloud_from_csv(args.input)

    # Export to GLB
    log.info(f"Exporting to {args.output}")
    export_to_glb(args.output)
    log.info("Export completed successfully")
