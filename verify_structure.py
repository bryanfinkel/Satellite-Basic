import os

def verify_project_structure(base_path):
    print("Project Structure Verification:")
    print("===============================")
    
    for root, dirs, files in os.walk(base_path):
        # Skip venv and git directories
        if 'venv' in root or '.git' in root:
            continue
            
        level = root.replace(base_path, '').count(os.sep)
        indent = '  ' * level
        folder = os.path.basename(root)
        print(f'{indent}{folder}/')
        
        for file in sorted(files):
            print(f'{indent}  {file}')

# Run the verification
verify_project_structure('.')