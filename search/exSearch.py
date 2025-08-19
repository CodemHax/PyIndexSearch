import asyncio
from utlis.config import file_index
import time
async def search_ext(extension):
    if not file_index:
        print("No index loaded.")
        return []
    start_time = time.time()
    paths = []
    ext_lower = extension.lower()
    if not ext_lower.startswith('.'):
        ext_lower = '.' + ext_lower
    for filename in file_index:
        if filename.lower().endswith(ext_lower):
            for filepath in file_index[filename]:
               paths.append(filepath)
        await asyncio.sleep(0)
    search_time = time.time() - start_time
    print(f"Extension search completed in {search_time:.4f}s")
    return paths