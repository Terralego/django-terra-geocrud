import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(ROOT, 'terra_geocrud', 'tests', 'data')
TEMPLATES_PATH = os.path.join(DATA_PATH, 'templates')
JSON_PATH = os.path.join(DATA_PATH, 'json')
SNAPSHOTS_PATH = os.path.join(DATA_PATH, 'snapshots')

LAYER_COMPOSANTES_SCHEMA = os.path.join(JSON_PATH, 'layer_composantes_schema.json')
FEATURE_PROPERTIES = os.path.join(JSON_PATH, 'feature_properties.json')

DOCX_PLAN_DE_GESTION = os.path.join(TEMPLATES_PATH, 'plan_gestion_composante.docx')
ODT_TEMPLATE = os.path.join(TEMPLATES_PATH, 'template.odt')

SNAPSHOT_PLAN_DE_GESTION = os.path.join(SNAPSHOTS_PATH, 'snapshot_plan_de_gestion.xml')
