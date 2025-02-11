import subprocess
import os
from pathlib import Path


def run_blender_process(
    input_csv: str,
    output_glb: str,
    blender_path: str = None,
    script_path: str = None,
) -> bool:
    """
    Executa o processo do Blender para criar o terreno a partir do CSV e exportar para GLB.

    Args:
        input_csv (str): Caminho completo para o arquivo CSV de entrada.
        output_glb (str): Caminho completo para o arquivo GLB de saída.
        blender_path (str): Caminho para o executável do Blender.
        script_path (str): Caminho para o script Python do Blender.

    Returns:
        bool: True se a exportação foi bem-sucedida, False caso contrário.
    """
    try:
        # Obtém os caminhos das variáveis de ambiente se não fornecidos
        blender_executable = blender_path or os.getenv("BLENDER_PATH")
        current_dir = Path(__file__).parent
        script_path = str(current_dir / "terrain_3d_blender.py")
        if not os.path.exists(script_path):
            raise ValueError(f"Script Python não encontrado em: {script_path}")

        blender_script = script_path or os.getenv("BLENDER_SCRIPT_PATH")

        if not blender_executable or not blender_script:
            raise ValueError(
                "Blender path e script path devem ser fornecidos ou definidos nas variáveis de ambiente"
            )

        print(f"Usando Blender em: {blender_executable}")
        print(f"Usando script em: {blender_script}")

        # Verifica se os arquivos existem
        if not os.path.exists(blender_executable):
            raise FileNotFoundError(
                f"Executável do Blender não encontrado: {blender_executable}"
            )
        if not os.path.exists(blender_script):
            raise FileNotFoundError(
                f"Script do Blender não encontrado: {blender_script}"
            )

        # Cria o diretório de saída se não existir
        os.makedirs(os.path.dirname(output_glb), exist_ok=True)

        # Comando para executar o Blender
        command = [
            blender_executable,
            "--background",
            "--python",
            blender_script,
            "--",
            input_csv,
            output_glb,
        ]

        print("Executando o comando Blender:")
        print(" ".join(command))

        # Executa o comando e captura a saída
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(blender_script),
        )

        # Imprime a saída do Blender para debug
        print("Saída do Blender:")
        print(result.stdout)
        if result.stderr:
            print("Erros do Blender:")
            print(result.stderr)

        # Verifica se o arquivo GLB foi criado e tem um tamanho razoável
        if os.path.exists(output_glb):
            file_size = os.path.getsize(output_glb)
            print(f"Tamanho do arquivo GLB exportado: {file_size} bytes")
            if file_size > 1000:
                print("Exportação concluída com sucesso!")
                return True
            else:
                print("ERRO: Arquivo GLB gerado está muito pequeno.")
                return False
        else:
            print("ERRO: Arquivo GLB não foi criado.")
            return False

    except Exception as e:
        print(f"Erro ao executar o processo Blender: {str(e)}")
        return False
