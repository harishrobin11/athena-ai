import os
import glob

files = glob.glob('app/ui/**/*.py', recursive=True)

for file in files:
    with open(file, 'r') as f:
        content = f.read()
    
    modified = False
    if "http://127.0.0.1:8000" in content or "http://localhost:8000" in content:
        if "import os" not in content:
            content = "import os\n" + content
            
        content = content.replace('"http://127.0.0.1:8000"', 'os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")')
        
        # Careful with f-strings or partial paths
        content = content.replace('f"http://localhost:8000', 'f"{os.getenv(\'BACKEND_API_URL\', \'http://127.0.0.1:8000\')}')
        content = content.replace('"http://localhost:8000', 'os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000") + "')
        modified = True
        
    if modified:
        with open(file, 'w') as f:
            f.write(content)
            
print("Done!")
