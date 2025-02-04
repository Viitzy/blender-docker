import bpy


def enable_addons():
    # Lista de add-ons para habilitar
    addons_to_enable = ["add_mesh_extra_objects", "sapling"]

    # Habilita cada add-on
    for addon in addons_to_enable:
        try:
            bpy.ops.preferences.addon_enable(module=addon)
            print(f"Add-on {addon} habilitado com sucesso!")
        except Exception as e:
            print(f"Erro ao habilitar add-on {addon}: {str(e)}")


if __name__ == "__main__":
    enable_addons()
