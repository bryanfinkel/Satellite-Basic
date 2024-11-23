import os

structure = {
    'app': {
        '__init__.py': '',
        'main.py': '# Main application file\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\nasync def root():\n    return {\"message\": \"Hello, World!\"}',
        'core': {
            '__init__.py': '',
            'config.py': '',
            'stac_client.py': '',
        },
        'api': {
            '__init__.py': '',
            'routes.py': '',
        },
        'services': {
            '__init__.py': '',
            'imagery_service.py': '',
            'flood_analysis.py': '',
            'vegetation_analysis.py': '',
            'infrastructure_analysis.py': '',
        },
        'utils': {
            '__init__.py': '',
            'helpers.py': '',
        }
    },
    'tests': {},
    'docker': {},
}

def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w') as f:
                f.write(content)

if __name__ == '__main__':
    create_structure('.', structure)