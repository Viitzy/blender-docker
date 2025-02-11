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
        script_path = str(current_dir / "generate_terrain_glb.py")
        if not os.path.exists(script_path):
            raise ValueError(f"Script Python não encontrado em: {script_path}")

        if not blender_executable:
            raise ValueError(
                "Blender path deve ser fornecido ou definido na variável de ambiente BLENDER_PATH"
            )

        print(f"Usando Blender em: {blender_executable}")
        print(f"Usando script em: {script_path}")
        print(f"Arquivo CSV de entrada: {input_csv}")
        print(f"Arquivo GLB de saída: {output_glb}")

        # Verifica se os arquivos existem
        if not os.path.exists(blender_executable):
            raise FileNotFoundError(
                f"Executável do Blender não encontrado: {blender_executable}"
            )
        if not os.path.exists(input_csv):
            raise FileNotFoundError(
                f"Arquivo CSV de entrada não encontrado: {input_csv}"
            )

        # Cria o diretório de saída se não existir
        os.makedirs(os.path.dirname(output_glb), exist_ok=True)

        # Comando para executar o Blender
        command = [
            blender_executable,
            "--background",
            "--python",
            script_path,
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
            cwd=os.path.dirname(script_path),
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
