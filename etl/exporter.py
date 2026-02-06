import json
import os
import tempfile
import shutil
from datetime import datetime

class Exporter:
    def __init__(self, output_dir="public/data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _sanitize(self, obj):
        """Recursively replace NaN/Infinity with None for valid JSON."""
        if isinstance(obj, float):
            import math
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, dict):
            return {k: self._sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize(v) for v in obj]
        return obj

    def export_json(self, data, filename, metadata=None):
        """
        Escreve dados para JSON de forma atômica.
        data: Dict ou List para serializar.
        filename: Nome do arquivo (ex: 'stocks.json').
        metadata: Dict extra para incluir no wrapper.
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Sanitize data to remove NaNs
        safe_data = self._sanitize(data)
        
        output_payload = {
            "generated_at": timestamp,
            "schema_version": "1.0",
            "data": safe_data
        }
        
        if metadata:
            output_payload.update(metadata)
            
        # Atomic Write
        # 1. Write to temp file
        # 2. Move to target location
        
        target_path = os.path.join(self.output_dir, filename)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tmp_file:
            json.dump(output_payload, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = tmp_file.name
            
        # Move atomic
        shutil.move(tmp_path, target_path)
        print(f"Exported {filename} to {target_path}")

    def export_excluded_list(self, excluded_data):
        """
        Exporta lista de exclusões.
        """
        self.export_json(excluded_data, "excluded_companies.json")
