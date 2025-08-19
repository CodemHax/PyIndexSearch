import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from utlis.config import INDEX_FILE, file_index, ensure_index_dir

def show_progress(current, total, prefix='Progress', suffix='Complete', length=50):
    if total == 0:
        return
    percent = "{0:.1f}".format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix} ({current}/{total})', end='\r')
    if current == total:
        print()

def check_files_batch(file_paths_batch):
    existing = []
    for file_path in file_paths_batch:
        if os.path.exists(file_path):
            existing.append(file_path)
    return existing

def scan_directory_chunk(path, skip_dirs=None):
    if skip_dirs is None:
        skip_dirs = set()

    files = []
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return files

        for item in path_obj.iterdir():
            if item.is_file():
                name = item.name
                if not name.startswith('.') and not name.endswith(('android', '.')):
                    files.append((name, str(item)))
            elif item.is_dir() and not item.name.startswith('.') and item.name not in skip_dirs:
                full_path_lower = str(item).lower()
                if 'appdata' in full_path_lower:
                    continue
                sub_files = scan_directory_chunk(item, skip_dirs)
                for sub_file in sub_files:
                    files.append(sub_file)
    except (PermissionError, OSError):
        pass
    return files

async def reindex_file(path):
    total_new = 0
    start = time.time()

    print("Checking existing files...")
    all_file_paths = []
    for filename, paths in file_index.items():
        for file_path in paths:
            all_file_paths.append(file_path)

    if all_file_paths:
        batch_size = max(100, len(all_file_paths) // 8)
        batches = []
        for i in range(0, len(all_file_paths), batch_size):
            batch = []
            for j in range(i, min(i + batch_size, len(all_file_paths))):
                batch.append(all_file_paths[j])
            batches.append(batch)

        valid_paths = set()
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            for batch in batches:
                futures.append(executor.submit(check_files_batch, batch))

            processed = 0
            for future in as_completed(futures):
                batch_result = future.result()
                for valid_path in batch_result:
                    valid_paths.add(valid_path)
                processed += 1
                show_progress(processed, len(batches), 'Checking', 'batches verified')

        print(f"\nCleaning up missing files...")
        files_to_remove = []
        for filename, paths in list(file_index.items()):
            new_paths = []
            for p in paths:
                if p in valid_paths:
                    new_paths.append(p)
            if new_paths:
                file_index[filename] = new_paths
            else:
                files_to_remove.append(filename)

        for filename in files_to_remove:
            del file_index[filename]

        removed_count = len(all_file_paths) - len(valid_paths)
        print(f"Removed {removed_count} missing files")

    print("Scanning for new files...")

    try:
        path_obj = Path(path)
        if not path_obj.exists():
            print(f"Path does not exist: {path}")
            return

        subdirs = [path]
        if path_obj.is_dir():
            try:
                for item in path_obj.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        subdirs.append(str(item))
            except (PermissionError, OSError):
                pass

        if len(subdirs) > 8:
            new_subdirs = []
            for i in range(8):
                new_subdirs.append(subdirs[i])
            subdirs = new_subdirs

        print(f"Scanning {len(subdirs)} directories in parallel...")

        with ThreadPoolExecutor(max_workers=min(6, len(subdirs))) as executor:
            futures = {}
            for subdir in subdirs:
                futures[executor.submit(scan_directory_chunk, subdir)] = subdir

            all_files = []
            completed = 0

            for future in as_completed(futures):
                subdir = futures[future]
                try:
                    result = future.result()
                    for file_info in result:
                        all_files.append(file_info)
                    completed += 1
                    print(f"\rScanned: {completed}/{len(subdirs)} directories, found {len(all_files)} files...", end='')
                except Exception as e:
                    print(f"\nError scanning {subdir}: {e}")

        print(f"\nFound {len(all_files)} files total")

        if not all_files:
            print("No new files found.")
            return

        existing_file_paths = set()
        for paths in file_index.values():
            for path_item in paths:
                existing_file_paths.add(path_item)

        new_files = []
        for file, file_path in all_files:
            if file_path not in existing_file_paths:
                new_files.append((file, file_path))

        if new_files:
            batch_size = 1000
            batches = []
            for i in range(0, len(new_files), batch_size):
                batch = []
                for j in range(i, min(i + batch_size, len(new_files))):
                    batch.append(new_files[j])
                batches.append(batch)

            processed = 0
            for batch in batches:
                for file, file_path in batch:
                    if file not in file_index:
                        file_index[file] = []
                    file_index[file].append(file_path)
                    total_new += 1

                processed += 1
                show_progress(processed, len(batches), 'Adding', 'new files processed')

        print(f"\nAdded {total_new} new files to index...")

    except Exception as e:
        print(f"Error during reindexing: {e}")

    try:
        ensure_index_dir()
        print("Saving updated index file...")
        with open(INDEX_FILE, 'w') as f:
            total_files = 0
            for paths in file_index.values():
                total_files += len(paths)
            json.dump({"file_index": file_index, "total_files": total_files}, f, indent=2)
        print("Index file saved successfully!")
    except Exception as e:
        print(f"Error saving reindex: {e}")

    reindex_time = time.time() - start
    files_per_second = total_new / reindex_time if reindex_time > 0 else 0
    print(f"Reindex completed in {reindex_time:.2f}s. Added {total_new} new files.")
    print(f"Speed: {files_per_second:.0f} files/second")
