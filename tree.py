import os

IGNORE = {"venv", ".venv", "__pycache__", "node_modules", ".git"}

def print_tree(start_path=".", prefix="", level=3):
    if level < 0:
        return
    try:
        entries = sorted(os.listdir(start_path))
    except PermissionError:
        return
    for i, name in enumerate(entries):
        if name in IGNORE or name.startswith('.'):
            continue
        path = os.path.join(start_path, name)
        connector = "└── " if i == len(entries)-1 else "├── "
        print(prefix + connector + name)
        if os.path.isdir(path):
            extension = "    " if i == len(entries)-1 else "│   "
            print_tree(path, prefix + extension, level-1)

print_tree(".", level=3)
