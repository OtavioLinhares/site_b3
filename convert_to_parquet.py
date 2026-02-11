"""
Otimização: Converter price_history.json (180MB) para Parquet

Parquet é ~10x menor e 100x mais rápido para ler
"""

import json
import pandas as pd
from pathlib import Path
import time

def convert_to_parquet():
    print("\n" + "="*80)
    print("🚀 CONVERTENDO JSON → PARQUET")
    print("="*80 + "\n")
    
    json_path = Path("data/processed/price_history.json")
    parquet_path = Path("data/processed/price_history.parquet")
    
    # Medir tamanho original
    original_size = json_path.stat().st_size / (1024*1024)  # MB
    print(f"📊 Arquivo original: {original_size:.1f} MB\n")
    
    # Carregar JSON
    print("⏳ Carregando JSON...")
    start = time.time()
    with open(json_path, 'r') as f:
        data = json.load(f)
    load_time = time.time() - start
    print(f"   ✅ Carregado em {load_time:.1f}s\n")
    
    # Converter para DataFrame único
    print("🔄 Convertendo para Parquet...")
    start = time.time()
    
    all_records = []
    for ticker, records in data.items():
        if not records:
            continue
        df = pd.DataFrame(records)
        df['ticker'] = ticker
        all_records.append(df)
    
    # Combinar tudo
    combined_df = pd.concat(all_records, ignore_index=True)
    
    # Normalizar nomes de colunas
    combined_df.columns = [c.lower() for c in combined_df.columns]
    
    if 'date' in combined_df.columns:
       combined_df['date'] = pd.to_datetime(combined_df['date'])
    
    # Salvar como Parquet com compressão
    combined_df.to_parquet(
        parquet_path,
        engine='pyarrow',
        compression='snappy',
        index=False
    )
    
    convert_time = time.time() - start
    print(f"   ✅ Convertido em {convert_time:.1f}s\n")
    
    # Comparar tamanhos
    parquet_size = parquet_path.stat().st_size / (1024*1024)  # MB
    reduction = ((original_size - parquet_size) / original_size) * 100
    
    print("📈 RESULTADOS:")
    print(f"   JSON:    {original_size:.1f} MB")
    print(f"   Parquet: {parquet_size:.1f} MB")
    print(f"   Redução: {reduction:.0f}%\n")
    
    # Testar velocidade de leitura
    print("⚡ Teste de Performance:")
    
    # JSON
    start = time.time()
    with open(json_path, 'r') as f:
        _ = json.load(f)
    json_read_time = time.time() - start
    print(f"   JSON leitura:    {json_read_time:.1f}s")
    
    # Parquet
    start = time.time()
    _ = pd.read_parquet(parquet_path)
    parquet_read_time = time.time() - start
    print(f"   Parquet leitura: {parquet_read_time:.2f}s")
    
    speedup = json_read_time / parquet_read_time
    print(f"   Speedup: {speedup:.0f}x mais rápido! 🚀\n")
    
    print("✅ Conversão concluída!")
    print(f"   Arquivo salvo em: {parquet_path}\n")

if __name__ == "__main__":
    convert_to_parquet()
