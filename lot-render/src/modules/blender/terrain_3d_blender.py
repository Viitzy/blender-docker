import bpy
import sys
import csv
import math
from mathutils import Vector


def clear_scene():
    """Limpa a cena atual"""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def create_terrain_from_csv(csv_path):
    """Cria o terreno a partir do arquivo CSV"""
    # Lê os pontos do CSV
    points = []
    with open(csv_path, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            x = float(row["x"])
            y = float(row["y"])
            z = float(row["z"])
            points.append((x, y, z))

    if not points:
        raise ValueError("Nenhum ponto encontrado no CSV")

    # Cria uma nova malha
    mesh = bpy.data.meshes.new("TerrainMesh")
    obj = bpy.data.objects.new("Terrain", mesh)

    # Adiciona o objeto à cena
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    # Cria os vértices
    vertices = [Vector(p) for p in points]

    # Cria as faces usando triangulação
    faces = []
    n = int(math.sqrt(len(points)))
    for i in range(n - 1):
        for j in range(n - 1):
            idx = i * n + j
            faces.append([idx, idx + 1, idx + n + 1, idx + n])

    # Atualiza a malha
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Suaviza a malha
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_smooth()

    return obj


def export_glb(output_path):
    """Exporta a cena para GLB"""
    bpy.ops.export_scene.gltf(
        filepath=output_path, export_format="GLB", use_selection=False
    )


def main():
    # Obtém argumentos da linha de comando
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        print(
            "Uso: blender --background --python script.py -- input.csv output.glb"
        )
        sys.exit(1)

    input_csv = args[0]
    output_glb = args[1]

    try:
        # Limpa a cena
        clear_scene()

        # Cria o terreno
        terrain = create_terrain_from_csv(input_csv)

        # Exporta para GLB
        export_glb(output_glb)

        print(f"Terreno exportado com sucesso para {output_glb}")

    except Exception as e:
        print(f"Erro ao gerar terreno: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
