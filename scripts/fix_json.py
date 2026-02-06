import json
import os
import math

TARGET = "public/data/b3_stocks.json"

def sanitize(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj

def fix_json():
    print(f"Reading {TARGET}...")
    try:
        # Read as string first to avoid json.load error on NaN if possible? 
        # Python json.load actually accepts NaN by default (converts to float('nan')). 
        # The issue is the user's browser (JS) rejecting it.
        # So we can load it in Python (it works), sanitize, and dump it back validly.
        
        with open(TARGET, 'r') as f:
            data = json.load(f)
            
        print("Sanitizing data...")
        clean_data = sanitize(data)
        
        print(f"Writing fixed JSON to {TARGET}...")
        with open(TARGET, 'w') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)
            
        print("Done! JSON should be valid now.")
        
    except Exception as e:
        print(f"Failed to fix JSON: {e}")

if __name__ == "__main__":
    fix_json()
