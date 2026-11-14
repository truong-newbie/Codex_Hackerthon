"""
Exports the FastAPI OpenAPI 3.x specification to admin-appsmith/openapi.json
for 1-click import into Appsmith REST Datasource or Postman.
"""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.main import app

def export_spec():
    out_path = ROOT_DIR / "admin-appsmith" / "openapi.json"
    spec = app.openapi()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"Exported OpenAPI spec ({len(spec.get('paths', {}))} paths) to {out_path}")

if __name__ == "__main__":
    export_spec()
