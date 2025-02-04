import bpy
import os


def verify_addon_files():
    """Verifica se os arquivos dos add-ons estão presentes"""
    # Verifica tanto no diretório do usuário quanto no diretório do Blender
    addon_paths = [
        bpy.utils.user_resource("SCRIPTS", path="addons"),
        os.path.join(bpy.utils.resource_path("LOCAL"), "scripts", "addons"),
    ]

    required_files = {
        "add_mesh_extra_objects": ["__init__.py"],
        "add_curve_sapling": [
            "__init__.py",
            "utils.py",
        ],  # Nome correto do módulo
    }

    for addon_path in addon_paths:
        print(f"Verificando add-ons em: {addon_path}")
        for addon, files in required_files.items():
            addon_dir = os.path.join(addon_path, addon)
            if os.path.exists(addon_dir):
                print(f"Diretório do add-on {addon} encontrado em {addon_dir}")
                for file in files:
                    file_path = os.path.join(addon_dir, file)
                    if os.path.exists(file_path):
                        print(
                            f"Arquivo {file} encontrado para o add-on {addon}"
                        )
                    else:
                        print(
                            f"Arquivo {file} não encontrado para o add-on {addon}"
                        )
            else:
                print(
                    f"Diretório do add-on {addon} não encontrado em {addon_dir}"
                )


def enable_addons():
    """Habilita os add-ons necessários"""
    # Primeiro verifica os arquivos
    verify_addon_files()

    # Lista de add-ons para habilitar
    addons_to_enable = [
        "add_mesh_extra_objects",
        "add_curve_sapling",
    ]  # Nome correto do módulo

    # Habilita cada add-on
    for addon in addons_to_enable:
        try:
            # Verifica se o add-on já está habilitado
            if addon in bpy.context.preferences.addons:
                print(f"Add-on {addon} já está habilitado!")
                continue

            print(f"Tentando habilitar {addon}...")
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
