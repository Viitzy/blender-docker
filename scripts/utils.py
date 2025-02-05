import bpy
import logging
import os

# Load default logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def delete_cube():
    """Delete cube created by default."""
    if "Cube" in bpy.data.objects:
        cube_obj = bpy.data.objects["Cube"]
        log.info("Remove default Cube object")
        bpy.data.objects.remove(cube_obj, do_unlink=True)

    # Also clean up the mesh data if it exists
    if "Cube" in bpy.data.meshes:
        mesh = bpy.data.meshes["Cube"]
        log.info("Remove default Cube mesh")
        bpy.data.meshes.remove(mesh)
