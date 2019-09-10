import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(ROOT, 'terra_crud', 'tests', 'data')
TEMPLATES_PATH = os.path.join(DATA_PATH, 'templates')

ODT_TEMPLATE = os.path.join(TEMPLATES_PATH, 'template.odt')

CONTENT_XML_PATH = os.path.join(DATA_PATH, 'content.xml')
