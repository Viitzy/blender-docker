from typing import List, Dict
import os
import json
import traceback
from .blender.blender_execution import run_blender_process


def process_lots_glb(
    input_dir: str,
    output_dir: str,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa lotes gerando arquivos GLB a partir dos CSVs locais.
    """
    print("\n=== Iniciando processamento de GLB ===")
    print(f"Filtro de confiança: >= {confidence}")

    try:
        # Cria diretório de saída se não existir
        os.makedirs(output_dir, exist_ok=True)

        print(f"Arquivos no diretório de entrada: {os.listdir(input_dir)}")
        # Lista todos os arquivos CSV no diretório de entrada
        csv_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
        print(f"\nTotal de arquivos para processar: {len(csv_files)}")

        processed_docs = []
        errors = 0

        for i, csv_file in enumerate(csv_files, 1):
            try:
                # Define nomes dos arquivos
                base_name = os.path.splitext(csv_file)[0]
                output_file = os.path.join(output_dir, f"{base_name}.glb")

                # Procura o JSON no diretório anterior (front)
                front_dir = os.path.dirname(input_dir)
                front_dir = os.path.join(front_dir, "front")
                json_file = os.path.join(front_dir, f"{base_name}.json")

                # Carrega o documento JSON original
                if not os.path.exists(json_file):
                    print(f"Arquivo JSON não encontrado: {json_file}")
                    continue

                with open(json_file, "r") as f:
                    doc = json.load(f)

                # Verifica a confiança
                confidence_value = doc.get("original_detection", {}).get(
                    "confidence", 0
                )
                if confidence_value < confidence:
                    print(
                        f"Confiança {confidence_value} abaixo do limiar, pulando..."
                    )
                    continue

                # Verifica se já existe arquivo processado
                if os.path.exists(output_file):
                    print(
                        f"\nArquivo {output_file} já processado, carregando dados..."
                    )
                    doc["glb_file"] = output_file
                    processed_docs.append(doc)
                    continue

                print(f"\nProcessando arquivo {i}/{len(csv_files)}")
                csv_path = os.path.join(input_dir, csv_file)

                # Executa processo do Blender
                print(f"Executando Blender para {csv_file}...")
                success = run_blender_process(
                    input_csv=csv_path, output_glb=output_file
                )

                if not success:
                    print(f"❌ Falha ao executar Blender para {csv_file}")
                    errors += 1
                    continue

                print(f"✓ GLB gerado com sucesso: {output_file}")
                doc["glb_file"] = output_file
                processed_docs.append(doc)

            except Exception as e:
                errors += 1
                print(f"Erro ao processar arquivo {csv_file}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de arquivos: {len(csv_files)}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        traceback.print_exc()
        return []
