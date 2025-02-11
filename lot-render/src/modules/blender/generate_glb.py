from typing import Optional, List
from pymongo import MongoClient
from google.cloud import storage
from bson import ObjectId
import tempfile
import os
from pathlib import Path
from blender.blender_execution import run_blender_process

def process_single_lot(
    client: MongoClient,
    csv_bucket_name: str,
    glb_bucket_name: str,
    doc: dict
) -> bool:
    """
    Processa um único lote, gerando o arquivo GLB a partir do CSV.
    
    Args:
        client: Cliente MongoDB
        csv_bucket_name: Nome do bucket GCS para CSVs
        glb_bucket_name: Nome do bucket GCS para GLBs
        doc: Documento do MongoDB
    
    Returns:
        bool: True se processado com sucesso, False caso contrário
    """
    try:
        object_id = str(doc['_id'])
        print(f"\nProcessando lote: {object_id}")
        
        # Verifica se já tem o arquivo GLB
        if "glb_elevation_file" in doc:
            print(f"⚠️ Lote já possui arquivo GLB: {doc['glb_elevation_file']}")
            return True
            
        # Verifica se tem o CSV
        if "csv_elevation_colors" not in doc:
            print(f"❌ Lote não possui CSV de elevação")
            return False
            
        # Configura cliente do Storage
        storage_client = storage.Client()
        csv_bucket = storage_client.bucket(csv_bucket_name)
        glb_bucket = storage_client.bucket(glb_bucket_name)
        
        # Extrai o caminho do CSV do URL
        csv_url = doc["csv_elevation_colors"]
        print(f"URL do CSV: {csv_url}")
        
        # Extrai o caminho relativo do arquivo no bucket
        # Remove a parte inicial da URL do GCS
        csv_path = csv_url.replace('https://storage.cloud.google.com/', '')
        # Remove o nome do bucket e a primeira barra
        csv_path = '/'.join(csv_path.split('/')[1:])
        print(f"Caminho do blob CSV: {csv_path}")
        
        # Cria diretório temporário
        with tempfile.TemporaryDirectory() as temp_dir:
            # Define caminhos dos arquivos
            temp_csv = Path(temp_dir) / f"{object_id}.csv"
            temp_glb = Path(temp_dir) / f"{object_id}.glb"
            
            print(f"Arquivo CSV temporário: {temp_csv}")
            print(f"Arquivo GLB temporário: {temp_glb}")
            
            # Download do CSV
            print(f"Baixando CSV: {csv_url}")
            blob = csv_bucket.blob(csv_path)
            blob.download_to_filename(temp_csv)
            
            # Verifica conteúdo do CSV
            with open(temp_csv, 'r') as f:
                print(f"\nPrimeiras 5 linhas do CSV:")
                for i, line in enumerate(f):
                    if i < 5:
                        print(line.strip())
                    else:
                        break
            
            # Executa processo do Blender
            print("\nExecutando Blender...")
            success = run_blender_process(
                input_csv=str(temp_csv),
                output_glb=str(temp_glb)
            )
            
            if not success:
                print("❌ Falha ao executar Blender")
                return False
                
            # Verifica se o GLB foi gerado e seu tamanho
            if os.path.exists(temp_glb):
                glb_size = os.path.getsize(temp_glb)
                print(f"\nTamanho do arquivo GLB gerado: {glb_size} bytes")
            else:
                print("❌ Arquivo GLB não foi gerado")
                return False
            
            # Define caminho no bucket para o GLB
            glb_blob_name = csv_path.replace('.csv', '.glb')
            print(f"Nome do blob GLB: {glb_blob_name}")
            
            # Upload do GLB
            print(f"Fazendo upload do GLB para {glb_bucket_name}...")
            glb_blob = glb_bucket.blob(glb_blob_name)
            glb_blob.upload_from_filename(temp_glb)
            
            # Gera URL pública
            glb_url = f"https://storage.googleapis.com/{glb_bucket_name}/{glb_blob_name}"
            
            # Atualiza documento no MongoDB
            client.streets.lots_detections_details.update_one(
                {"_id": doc["_id"]},
                {"$set": {"glb_elevation_file": glb_url}}
            )
            
            print(f"✅ GLB gerado e salvo: {glb_url}")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao processar lote {object_id}: {str(e)}")
        return False

def process_lots_glb(
    mongodb_uri: str,
    google_place_id: str,
    year: str,
    doc_id: Optional[str] = None,
    csv_bucket_name: str = "csv_from_lots_details",
    glb_bucket_name: str = "glb_from_lots_details",
    confidence: float = 0.62
) -> None:
    """
    Processa lotes gerando arquivos GLB a partir dos CSVs.
    
    Args:
        mongodb_uri (str): URI de conexão com MongoDB
        google_place_id: ID do Google Place
        year: Ano dos documentos
        doc_id: ID específico do documento (opcional)
        csv_bucket_name: Nome do bucket GCS para CSVs
        glb_bucket_name: Nome do bucket GCS para GLBs
        confidence (float): Valor mínimo de confiança para processar o documento (default: 0.62)
    """
    client = None
    try:
        # Estabelece conexão com MongoDB
        client = MongoClient(mongodb_uri)
        
        # Prepara filtro do MongoDB
        mongo_filter = {
            "google_place_id": google_place_id,
            "year": year,
            "confidence": {"$gte": confidence}
        }
        
        if doc_id:
            mongo_filter["_id"] = ObjectId(doc_id)
            
        # Busca documentos
        docs = list(client.streets.lots_detections_details.find(mongo_filter))
        
        if not docs:
            print(f"Nenhum documento encontrado para os filtros:")
            print(f"Google Place ID: {google_place_id}")
            print(f"Ano: {year}")
            print(f"Confiança mínima: {confidence}")
            if doc_id:
                print(f"Doc ID: {doc_id}")
            return
            
        print("\n=== Iniciando processamento de GLB ===")
        print(f"Total de documentos: {len(docs)}")
        print(f"Filtro de confiança: >= {confidence}")
        
        # Processa cada documento
        success_count = 0
        error_count = 0
        
        for doc in docs:
            if process_single_lot(client, csv_bucket_name, glb_bucket_name, doc):
                success_count += 1
            else:
                error_count += 1
                
        print("\n=== Resumo do processamento ===")
        print(f"Total processado: {len(docs)}")
        print(f"Sucessos: {success_count}")
        print(f"Erros: {error_count}")
        
    except Exception as e:
        print(f"❌ Erro no processamento: {str(e)}")
        raise 
        
    finally:
        # Fecha a conexão com segurança
        if client:
            try:
                client.close()
                print("✅ Conexão com MongoDB fechada com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao fechar conexão com MongoDB: {e}") 