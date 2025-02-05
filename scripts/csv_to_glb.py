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

    # Create mesh from vertices
    mesh.from_pydata(vertices, [], [])
    mesh.update()

    # Add vertex colors
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()

    color_layer = mesh.vertex_colors[0]
    for i, color in enumerate(colors):
        color_layer.data[i].color = color

    return obj


def export_to_glb(output_path):
    """Export the scene to GLB format."""
    bpy.ops.export_scene.gltf(
        filepath=output_path, export_format="GLB", use_selection=False
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
