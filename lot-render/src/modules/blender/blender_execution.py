import os
import subprocess
from pathlib import Path


def run_blender_process(
    input_csv: str,
    output_glb: str,
) -> bool:
    """
    Executa o processo do Blender para gerar o GLB.

    Args:
        input_csv: Caminho para o arquivo CSV de entrada
        output_glb: Caminho para o arquivo GLB de saída

    Returns:
        bool: True se o processo foi executado com sucesso
    """
    try:
        # Obtém o caminho do Blender da variável de ambiente
        blender_path = os.getenv("BLENDER_PATH", "/usr/local/blender/blender")
        if not os.path.exists(blender_path):
            raise ValueError(f"Blender não encontrado em: {blender_path}")

        # Obtém o caminho do script Python
        current_dir = Path(__file__).parent
        script_path = str(current_dir / "terrain_3d_blender.py")
        if not os.path.exists(script_path):
            raise ValueError(f"Script Python não encontrado em: {script_path}")

        print(f"Usando Blender em: {blender_path}")
        print(f"Usando script em: {script_path}")

        # Monta o comando
        command = [
            blender_path,
            "--background",
            "--python",
            script_path,
            "--",
            input_csv,
            output_glb,
        ]

        # Executa o processo
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )

        # Verifica se o arquivo foi gerado
        if not os.path.exists(output_glb):
            print("Arquivo GLB não foi gerado")
            print("Saída do Blender:", result.stdout)
            print("Erro do Blender:", result.stderr)
            return False

        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o Blender: {str(e)}")
        print("Saída:", e.stdout)
        print("Erro:", e.stderr)
        return False
    except Exception as e:
        print(f"Erro ao executar o processo Blender: {str(e)}")
        return False
