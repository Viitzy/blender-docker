import bpy
import os


def verify_addon_files():
    """Verifica se os arquivos dos add-ons estão presentes"""
    addon_path = bpy.utils.user_resource("SCRIPTS", path="addons")
    required_files = {
        "add_mesh_extra_objects": ["__init__.py"],
        "sapling": ["__init__.py", "utils.py"],
    }

    for addon, files in required_files.items():
        addon_dir = os.path.join(addon_path, addon)
        if not os.path.exists(addon_dir):
            print(f"Diretório do add-on {addon} não encontrado em {addon_dir}")
            continue

        for file in files:
            file_path = os.path.join(addon_dir, file)
            if not os.path.exists(file_path):
                print(f"Arquivo {file} não encontrado para o add-on {addon}")
            else:
                print(f"Arquivo {file} encontrado para o add-on {addon}")


def enable_addons():
    """Habilita os add-ons necessários"""
    # Primeiro verifica os arquivos
    verify_addon_files()

    # Lista de add-ons para habilitar
    addons_to_enable = ["add_mesh_extra_objects", "sapling"]

    # Habilita cada add-on
    for addon in addons_to_enable:
        try:
            # Verifica se o add-on já está habilitado
            if addon in bpy.context.preferences.addons:
                print(f"Add-on {addon} já está habilitado!")
                continue

            bpy.ops.preferences.addon_enable(module=addon)

            # Verifica se foi habilitado com sucesso
            if addon in bpy.context.preferences.addons:
                print(f"Add-on {addon} habilitado com sucesso!")
            else:
                print(f"Falha ao habilitar add-on {addon}")

        except Exception as e:
            print(f"Erro ao habilitar add-on {addon}: {str(e)}")


if __name__ == "__main__":
    enable_addons()
