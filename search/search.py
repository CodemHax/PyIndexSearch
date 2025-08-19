import asyncio
import time
from utlis.config import file_index, folder_index
async def search_files(query):
    if not file_index and not folder_index:
        print("No file index found. Please run indexing first.")
        return []

    if query.startswith('-f '):
        return await search_folders_only(query[3:])
    elif query.startswith('-s '):
        return await search_both(query[3:])
    else:
        return await search_combined(query)

async def search_folders_only(query):
    start = time.time()
    match_paths = []
    query_lower = query.lower()

    for folder_name in folder_index:
        for folder_path in folder_index[folder_name]:
            folder_path_lower = folder_path.lower()
            if query_lower in folder_path_lower:
                parent_path = folder_path
                for sub_folder_name in folder_index:
                    for sub_folder_path in folder_index[sub_folder_name]:
                        if sub_folder_path.lower().startswith(parent_path.lower() + '\\') or sub_folder_path.lower().startswith(parent_path.lower() + '/'):
                            if sub_folder_path not in match_paths:
                                match_paths.append(sub_folder_path)
        await asyncio.sleep(0)

    search_time = time.time() - start
    print(f"Folder search completed in {search_time:.4f}s. Found {len(match_paths)} folder matches.")
    return match_paths

async def search_both(query):
    start = time.time()
    match_paths = []
    query_lower = query.lower()

    for folder_name in folder_index:
        if query_lower in folder_name.lower():
            for folder_path in folder_index[folder_name]:
                match_paths.append(folder_path)

    for file_name in file_index:
        if query_lower in file_name.lower():
            for file_path in file_index[file_name]:
                match_paths.append(file_path)
        await asyncio.sleep(0)

    search_time = time.time() - start
    print(f"Combined search completed in {search_time:.4f}s. Found {len(match_paths)} matches.")
    return match_paths

async def search_combined(query):
    start = time.time()
    match_paths = []
    query_lower = query.lower()

    for file in file_index:
        for file_path in file_index[file]:
            file_path_lower = file_path.lower()
            if query_lower in file.lower():
                match_paths.append(file_path)
            elif query_lower in file_path_lower:
                match_paths.append(file_path)
        await asyncio.sleep(0)

    search_time = time.time() - start
    print(f"Search completed in {search_time:.4f}s. Found {len(match_paths)} matches.")
    return match_paths
