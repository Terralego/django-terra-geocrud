import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(ROOT, 'terra_geocrud', 'tests', 'data')
TEMPLATES_PATH = os.path.join(DATA_PATH, 'templates')
JSON_PATH = os.path.join(DATA_PATH, 'json')
PICTURES_PATH = os.path.join(DATA_PATH, 'pictures')
SNAPSHOTS_PATH = os.path.join(DATA_PATH, 'snapshots')

with open(os.path.join(JSON_PATH, 'layer_schema.json'), 'rb') as schema_json:
    LAYER_SCHEMA = json.loads(schema_json.read())

with open(os.path.join(JSON_PATH, 'feature_properties.json'), 'rb') as feature_properties:
    FEATURE_PROPERTIES = json.loads(feature_properties.read())

DOCX_TEMPLATE = os.path.join(TEMPLATES_PATH, 'complex_template.docx')
PDF_TEMPLATE = os.path.join(TEMPLATES_PATH, 'pdf_template.pdf.html')
SMALL_PICTURE = os.path.join(PICTURES_PATH, 'small_picture.png')
with open(os.path.join(PICTURES_PATH, 'small_picture.png'), 'rb') as small_picture:
    SMALL_PICTURE = small_picture.read()
