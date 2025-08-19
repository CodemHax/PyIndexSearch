import os

INDEX_DIR = os.path.join(os.path.dirname(__file__), '..', 'index_data')
INDEX_FILE = os.path.join(INDEX_DIR, 'file_index.json')
file_index = {}
folder_index = {}

def ensure_index_dir():
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)
