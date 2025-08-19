import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from utlis.config import INDEX_FILE, file_index, folder_index, ensure_index_dir

def show_progress(current, total, prefix='Progress', suffix='Complete', length=50):
    if total == 0:
        return
    percent = "{0:.1f}".format(100 * (current / float(total)))
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix} ({current}/{total})', end='\r')
    if current == total:
        print()

def scan_directory_chunk(path, skip_dirs=None):
    if skip_dirs is None:
        skip_dirs = set()

    files = []
    folders = []
    scanned_dirs = []
    try:
        path_obj = Path(path)
        if not path_obj.exists():
            return files, folders, scanned_dirs

        print(f"Scanning directory: {path}")
        scanned_dirs.append(str(path))

        for item in path_obj.iterdir():
            if item.is_file():
                name = item.name
                if not name.startswith('.') and not name.endswith(('android', '.')):
                    files.append((name, str(item)))
            elif item.is_dir() and not item.name.startswith('.') and item.name not in skip_dirs:
                full_path_lower = str(item).lower()
                if 'appdata' in full_path_lower:
                    print(f"Skipping AppData directory: {item}")
                    continue
                folders.append((item.name, str(item)))
                sub_files, sub_folders, sub_dirs = scan_directory_chunk(item, skip_dirs)
                for sub_file in sub_files:
                    files.append(sub_file)
                for sub_folder in sub_folders:
                    folders.append(sub_folder)
                scanned_dirs.extend(sub_dirs)
    except (PermissionError, OSError):
        print(f"Permission denied or error accessing: {path}")
        pass
    return files, folders, scanned_dirs

def process_files_batch(files_batch):
    batch_index = {}
    for file, file_path in files_batch:
        if file not in batch_index:
            batch_index[file] = []
        batch_index[file].append(file_path)
    return batch_index

async def index(path):
    total = 0
    start = time.time()
    file_index.clear()

    print("Indexing files...")

    try:
        path_obj = Path(path)
        if not path_obj.exists():
            print(f"Path does not exist: {path}")
            return file_index

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
            all_folders = []
            all_scanned_dirs = []
            completed = 0

            for future in as_completed(futures):
                subdir = futures[future]
                try:
                    files, folders, dirs = future.result()
                    for file_info in files:
                        all_files.append(file_info)
                    for folder_info in folders:
                        all_folders.append(folder_info)
                    all_scanned_dirs.extend(dirs)
                    completed += 1
                    print(f"\rScanned: {completed}/{len(subdirs)} directories, found {len(all_files)} files...", end='')
                except Exception as e:
                    print(f"\nError scanning {subdir}: {e}")

        print(f"\nFound {len(all_files)} files total")
        print(f"Found {len(all_folders)} folders total")
        print(f"Scanned {len(all_scanned_dirs)} directories total")

        # Process folders
        folder_index.clear()
        for folder_name, folder_path in all_folders:
            if folder_name not in folder_index:
                folder_index[folder_name] = []
            folder_index[folder_name].append(folder_path)

        if not all_files:
            print("No files found to index.")
            return file_index

        batch_size = 1000
        batches = []
        for i in range(0, len(all_files), batch_size):
            batch = []
            for j in range(i, min(i + batch_size, len(all_files))):
                batch.append(all_files[j])
            batches.append(batch)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for batch in batches:
                futures.append(executor.submit(process_files_batch, batch))

            processed = 0
            for future in as_completed(futures):
                batch_result = future.result()

                for file, paths in batch_result.items():
                    if file not in file_index:
                        file_index[file] = []
                    for path_item in paths:
                        file_index[file].append(path_item)
                        total += 1

                processed += 1
                show_progress(processed, len(batches), 'Processing', 'batches completed')

    except Exception as e:
        print(f"Error during indexing: {e}")
        return file_index

    print(f"\nTotal files indexed: {total}")

    try:
        ensure_index_dir()
        print("Saving index file...")
        with open(INDEX_FILE, 'w') as f:
            json.dump({
                "file_index": file_index,
                "folder_index": folder_index,
                "total_files": total,
                "total_folders": len(all_folders),
                "scanned_directories": all_scanned_dirs,
                "scan_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        print("Index file saved successfully!")
    except Exception as e:
        print(f"Error saving index: {e}")

    build_time = time.time() - start
    unique_names = len(file_index)
    files_per_second = total / build_time if build_time > 0 else 0
    print(f"Index built in {build_time:.2f}s. Indexed {total} files with {unique_names} unique filenames.")
    print(f"Speed: {files_per_second:.0f} files/second")
    return file_index
