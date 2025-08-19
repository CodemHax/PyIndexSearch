from utlis.config import INDEX_FILE, file_index, folder_index
import os
import json

async def load_data():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            loaded_file_index = index_data.get('file_index', {})
            loaded_folder_index = index_data.get('folder_index', {})
            file_index.clear()
            folder_index.clear()
            file_index.update(loaded_file_index)
            folder_index.update(loaded_folder_index)
            print(f"Loaded index from {INDEX_FILE}: {len(file_index)} unique filenames, {len(folder_index)} unique folder names.")
        except UnicodeDecodeError:
            print(f"Index file appears to be corrupted or in wrong format. Deleting and starting fresh.")
            try:
                os.remove(INDEX_FILE)
                file_index.clear()
                folder_index.clear()
                print("Corrupted index file removed. Use 'index' command to create a new one.")
            except Exception as e:
                print(f"Could not remove corrupted file: {e}")
        except json.JSONDecodeError:
            print(f"Index file contains invalid JSON. Deleting and starting fresh.")
            try:
                os.remove(INDEX_FILE)
                file_index.clear()
                folder_index.clear()
                print("Invalid index file removed. Use 'index' command to create a new one.")
            except Exception as e:
                print(f"Could not remove invalid file: {e}")
        except Exception as e:
            print(f"Failed to load index: {e}")
    else:
        print(f"No index file found. Starting with empty index.")
