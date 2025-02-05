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


def create_terrain_from_csv(csv_path, depth=20.0):
    """Create a volumetric terrain mesh from CSV data with consistent depth."""
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

    # Find the minimum z value to calculate relative heights
    min_z = np.min(points[:, 2])
    max_z = np.max(points[:, 2])
    elevation_range = max_z - min_z
    log.info(f"Terrain elevation range: {elevation_range} units")

    # Create triangulation in 2D (using x,y coordinates)
    tri = Delaunay(points[:, :2])

    # Create vertices for top and bottom surfaces
    vertices_top = points.tolist()

    # Calculate bottom vertices with consistent depth from each point
    vertices_bottom = []
    for point in points:
        # Calculate the depth for this point
        # The depth will be constant (20.0) plus the elevation difference from the lowest point
        point_elevation = point[2] - min_z
        total_depth = depth + point_elevation
        vertices_bottom.append([point[0], point[1], point[2] - total_depth])

    vertices = vertices_top + vertices_bottom

    # Create faces for top and bottom surfaces
    faces_top = tri.simplices.tolist()
    faces_bottom = [[i + len(points) for i in face] for face in faces_top]
    # Reverse bottom face orientation
    faces_bottom = [face[::-1] for face in faces_bottom]

    # Create side walls by connecting top and bottom vertices
    # First, find boundary edges
    edges = set()
    for face in faces_top:
        for i in range(3):
            edge = tuple(sorted([face[i], face[(i + 1) % 3]]))
            if edge in edges:
                edges.remove(edge)
            else:
                edges.add(edge)

    # Create side wall faces
    side_faces = []
    for edge in edges:
        v1, v2 = edge
        # Create quad face: [top1, top2, bottom2, bottom1]
        side_faces.append([v1, v2, v2 + len(points), v1 + len(points)])

    # Combine all faces
    faces = faces_top + faces_bottom + side_faces

    # Create the mesh
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Add vertex colors
    if not mesh.vertex_colors:
        mesh.vertex_colors.new()

    color_layer = mesh.vertex_colors.active

    # Function to get darker color for bottom and sides
    def darken_color(color, factor=0.5):
        return (
            color[0] * factor,
            color[1] * factor,
            color[2] * factor,
            color[3],
        )

    # Apply colors to faces
    for poly in mesh.polygons:
        is_bottom = all(
            v >= len(points) for v in poly.vertices
        )  # Check if it's a bottom face
        is_side = (
            any(v >= len(points) for v in poly.vertices) and not is_bottom
        )  # Check if it's a side face

        for idx, loop_idx in enumerate(poly.loop_indices):
            vert_idx = poly.vertices[idx]
            original_color_idx = (
                vert_idx if vert_idx < len(points) else vert_idx - len(points)
            )
            color = colors[original_color_idx]

            if is_bottom:
                color = darken_color(color, 0.3)  # Darker for bottom
            elif is_side:
                color = darken_color(color, 0.7)  # Slightly darker for sides

            color_layer.data[loop_idx].color = color

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True

    # Add material
    mat = bpy.data.materials.new(name="TerrainMaterial")
    mat.use_nodes = True
    mat.use_backface_culling = False  # Show back faces

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
    parser.add_argument(
        "--depth", type=float, default=20.0, help="Base terrain depth/thickness"
    )
    args = parser.parse_args(argv)

    # Clear existing mesh objects
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Create terrain from CSV
    log.info(f"Creating terrain from {args.input}")
    terrain = create_terrain_from_csv(args.input, args.depth)

    # Export to GLB
    log.info(f"Exporting to {args.output}")
    export_to_glb(args.output)
    log.info("Export completed successfully")
