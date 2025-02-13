from typing import List, Dict, Optional
import os
import json
import traceback
from pymongo import MongoClient
from bson import ObjectId
from google.cloud import storage
import tempfile
from .blender.blender_execution import run_blender_process


def process_lots_glb(
    mongodb_uri: str,
    bucket_name: str,
    doc_id: Optional[str] = None,
    confidence: float = 0.62,
) -> List[Dict]:
    """
    Processa lotes gerando arquivos GLB a partir dos CSVs.

    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        bucket_name (str): Nome do bucket GCS
        doc_id (Optional[str]): ID específico do documento
        confidence (float): Valor mínimo de confiança

    Returns:
        List[Dict]: Lista de documentos processados
    """
    print("\n=== Iniciando processamento de GLB ===")
    print(f"Filtro de confiança: >= {confidence}")

    client = None
    storage_client = None
    try:
        # Inicializa cliente do GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        db = client["gethome-01-hml"]
        collection = db["lots_detections_details_hmg"]

        # Define query base
        query = {
            "$and": [
                {"csv_elevation_colors": {"$exists": True}},
                {"glb_elevation_file": {"$exists": False}},
                {"detection_result.confidence": {"$gte": confidence}},
            ]
        }

        # Se foi especificado um ID, adiciona à query
        if doc_id:
            query["_id"] = ObjectId(doc_id)

        total_docs = collection.count_documents(query)
        print(f"\nTotal de documentos para processar: {total_docs}")

        if total_docs == 0:
            print("Nenhum documento encontrado para processar")
            return []

        processed_docs = []
        errors = 0

        for doc in collection.find(query):
            try:
                current_doc_id = str(doc["_id"])
                print(f"\nProcessando documento {current_doc_id}")

                # Obtém URL do CSV
                csv_url = doc["csv_elevation_colors"]

                # Cria diretório temporário para trabalhar com os arquivos
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Define caminhos temporários
                    temp_csv = os.path.join(temp_dir, f"{current_doc_id}.csv")
                    temp_glb = os.path.join(temp_dir, f"{current_doc_id}.glb")

                    # Download do CSV do GCS
                    csv_blob_path = csv_url.replace(
                        f"https://storage.cloud.google.com/{bucket_name}/", ""
                    )
                    csv_blob = bucket.blob(csv_blob_path)
                    csv_blob.download_to_filename(temp_csv)

                    # Executa processo do Blender
                    print(f"Executando Blender para {current_doc_id}...")
                    success = run_blender_process(
                        input_csv=temp_csv, output_glb=temp_glb
                    )

                    if not success:
                        print(
                            f"❌ Falha ao executar Blender para {current_doc_id}"
                        )
                        errors += 1
                        continue

                    # Upload do GLB para GCS
                    glb_blob_path = f"glb_files/{current_doc_id}.glb"
                    glb_blob = bucket.blob(glb_blob_path)
                    glb_blob.upload_from_filename(temp_glb)

                    # Gera URL pública
                    glb_url = f"https://storage.cloud.google.com/{bucket_name}/{glb_blob_path}"

                    # Atualiza o documento com a URL do GLB
                    result = collection.update_one(
                        {"_id": ObjectId(current_doc_id)},
                        {"$set": {"glb_elevation_file": glb_url}},
                    )

                    if result.modified_count > 0:
                        print(f"✓ GLB gerado e salvo com sucesso: {glb_url}")
                        # Obtém o documento atualizado
                        updated_doc = collection.find_one(
                            {"_id": ObjectId(current_doc_id)}
                        )
                        processed_docs.append(updated_doc)
                    else:
                        print(
                            f"⚠️ Documento {current_doc_id} não foi atualizado"
                        )
                        errors += 1

            except Exception as e:
                errors += 1
                print(f"Erro ao processar documento {current_doc_id}: {str(e)}")
                traceback.print_exc()
                continue

        print("\n=== Resumo do processamento ===")
        print(f"Total de documentos: {total_docs}")
        print(f"Processados com sucesso: {len(processed_docs)}")
        print(f"Erros: {errors}")
        print("============================\n")

        return processed_docs

    except Exception as e:
        print(f"Erro durante o processamento: {str(e)}")
        traceback.print_exc()
        return []

    finally:
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}")
        if storage_client:
            try:
                storage_client.close()
                print("✅ Conexão com GCS fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com GCS: {e}")
