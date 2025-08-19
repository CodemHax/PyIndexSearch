import os
from utlis.config import INDEX_FILE, file_index, ensure_index_dir
from core.index import index
from core.reindex import reindex_file
from search.search import search_files
from search.exSearch import search_ext
from utlis.load import load_data

def print_banner():
    print("=" * 60)
    print(" 🔍 FILE SEARCH ENGINE")
    print("=" * 60)
    print(" Commands: search, exsearch, index, reindex, load, delete, help, exit")
    print("=" * 60)

def display(results, query):
    if not results:
        print(f"No files found matching '{query}'")
        return

    print(f"Found {len(results)} matches:")
    print("-" * 40)
    for i, file_path in enumerate(results, 1):
        clean_path = file_path.replace('\\', '/')
        filename = os.path.basename(file_path)
        print(f"{i:2d}. {filename}")

        print(f"    {clean_path}...")
    print("-" * 40)

def show_help():
    print("\nAvailable commands:")
    print("  search <query>     - Search for files by name")
    print("  exsearch <ext>     - Search for files by extension")
    print("  index              - Build/rebuild file index")
    print("  reindex            - Reindex existing files")
    print("  load               - Load existing index file")
    print("  delete             - Delete the index file")
    print("  help               - Show this help")
    print("  exit               - Exit program")

async def run_console():
    ensure_index_dir()
    print_banner()

    if os.path.exists(INDEX_FILE):
        await load_data()
    else:
        print("Index file not found. Use 'index' command to create one.")

    while True:
        try:
            cmd = input('\nsearch> ').strip()

            if not cmd:
                continue

            parts = cmd.split(' ', 1)
            command = parts[0].lower()

            if command in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            elif command == 'help':
                show_help()
            elif command == 'delete':
                if os.path.exists(INDEX_FILE):
                    confirm = input(f"Delete index file? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        os.remove(INDEX_FILE)
                        file_index.clear()
                        print("Index file deleted successfully!")
                    else:
                        print("Delete cancelled.")
                else:
                    print("No index file found to delete.")
            elif command == 'index':
                path = input('Enter path to index: ').strip()
                if path and os.path.exists(path):
                    print(f"Building file index for: {path}")
                    await index(path)
                    print("Index complete!")
                elif path:
                    print(f"Path not found: {path}")
                else:
                    print("No path provided")
            elif command == 'reindex':
                path = input('Enter path to reindex: ').strip()
                if path and os.path.exists(path):
                    print(f"Reindexing: {path}")
                    await reindex_file(path)
                    print("Reindex complete!")
                elif path:
                    print(f"Path not found: {path}")
                else:
                    print("No path provided")
            elif command == 'load':
                if os.path.exists(INDEX_FILE):
                    await load_data()
                    print("Index reloaded successfully!")
                else:
                    print(f"Index file not found: {INDEX_FILE}")
            elif command == 'search':
                if len(parts) > 1:
                    query = parts[1]
                else:
                    query = input('Enter search query: ').strip()
                if query:
                    results = await search_files(query)
                    display(results, query)
            elif command == 'exsearch':
                if len(parts) > 1:
                    extension = parts[1]
                else:
                    extension = input('Enter file extension: ').strip()
                if extension:
                    results = await search_ext(extension)
                    display(results, extension)
            else:
                print(f"Unknown command: '{command}'")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
