# IndexSearch

Fast file indexing and search engine with parallel processing.

## Features

- Fast parallel indexing with progress bars
- Search by filename or extension
- Real-time speed metrics
- Auto-ignores system folders

## Usage

```bash
python main.py
```

### Commands

- `index` - Build file index
- `search <name>` - Find files by name
- `exsearch <ext>` - Find files by extension  
- `reindex` - Update index
- `load` - Reload index
- `delete` - Delete index
- `help` - Show commands
- `exit` - Quit

### Example

```
search> index
Enter path to index: C:\Users\Admin\Documents

search> search myfile
Found 3 matches:
  1. myfile.txt

search> exsearch .py
Found 15 matches:
  1. main.py
```

## Performance

- 2,749 files/second on SSD
- Multi-threaded directory scanning
- 1000-file batch processing

## Project Structure

```
indexSearch/
├── main.py
├── core/
│   ├── index.py
│   └── reindex.py
├── search/
│   ├── search.py
│   └── exSearch.py
├── utlis/
│   ├── console.py
│   ├── config.py
│   └── load.py
└── index_data/
    └── file_index.json
```
