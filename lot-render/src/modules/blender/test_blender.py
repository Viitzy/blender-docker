import os
from pathlib import Path
from dotenv import load_dotenv
from src.blender.blender_execution import run_blender_process
from src.algorithms.execute import process_lots_glb


def test_blender_setup():
    """
    Testa a configuração do Blender executando um processo simples.
    """
    # Carrega variáveis de ambiente
    ROOT_DIR = Path(__file__).parent.parent.parent
    load_dotenv(dotenv_path=ROOT_DIR / ".env")

    # Obtém caminhos do Blender
    blender_path = os.getenv("BLENDER_PATH")
    script_path = os.getenv("BLENDER_SCRIPT_PATH")

    # Define caminhos de teste
    test_dir = ROOT_DIR / "test_outputs"
    os.makedirs(test_dir, exist_ok=True)

    test_csv = str(ROOT_DIR / "test_data/")
    test_output = str(test_dir / "test_terrain.glb")

    print("=== Iniciando teste do Blender ===")
    print(f"Blender Path: {blender_path}")
    print(f"Script Path: {script_path}")
    print(f"Test CSV: {test_csv}")
    print(f"Test Output: {test_output}")

    # Tenta executar o Blender
    # success = run_blender_process(
    #     input_csv=test_csv,
    #     output_glb=test_output,
    #     blender_path=blender_path,
    #     script_path=script_path,
    # )
    success = process_lots_glb(
        input_dir=test_csv,
        output_dir=test_output,
        confidence=0.62,
    )

    if success:
        print("✅ Teste do Blender concluído com sucesso!")
        print(f"Arquivo GLB gerado em: {test_output}")
    else:
        print("❌ Falha no teste do Blender")
        # Tenta ler o arquivo de crash
        crash_file = "/tmp/blender.crash.txt"
        if os.path.exists(crash_file):
            print("\nConteúdo do arquivo de crash:")
            with open(crash_file, "r") as f:
                print(f.read())


if __name__ == "__main__":
    test_blender_setup()
