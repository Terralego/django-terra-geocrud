import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(ROOT, 'terra_geocrud', 'tests', 'data')
TEMPLATES_PATH = os.path.join(DATA_PATH, 'templates')
JSON_PATH = os.path.join(DATA_PATH, 'json')
PICTURES_PATH = os.path.join(DATA_PATH, 'pictures')
SNAPSHOTS_PATH = os.path.join(DATA_PATH, 'snapshots')

LAYER_SCHEMA = os.path.join(JSON_PATH, 'layer_schema.json')
FEATURE_PROPERTIES = os.path.join(JSON_PATH, 'feature_properties.json')

DOCX_TEMPLATE = os.path.join(TEMPLATES_PATH, 'complex_template.docx')

SMALL_PICTURE = os.path.join(PICTURES_PATH, 'small_picture.png')
