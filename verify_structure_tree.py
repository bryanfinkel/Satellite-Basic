import os

def print_tree(directory, prefix=''):
    # Get and sort directory contents
    entries = sorted(os.listdir(directory))
    entries = [e for e in entries if e not in ['.git', 'venv', '__pycache__']]
    
    # Count directories for proper line drawing
    dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e))]
    files = [e for e in entries if not os.path.isdir(os.path.join(directory, e))]
    
    # Process all files first
    for i, entry in enumerate(files):
        connector = '└── ' if i == len(files) - 1 and not dirs else '├── '
        print(f'{prefix}{connector}{entry}')

    # Then process directories
    for i, entry in enumerate(dirs):
        connector = '└── ' if i == len(dirs) - 1 else '├── '
        print(f'{prefix}{connector}{entry}/')
        extension = '    ' if i == len(dirs) - 1 else '│   '
        print_tree(os.path.join(directory, entry), prefix + extension)

print("Satellite-Basic/")
print_tree('.')