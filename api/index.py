import sys
import os

# Ensure backend directory is in sys.path regardless of Vercel serverless directory structure
cwd = os.getcwd()
file_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(file_dir)

path_candidates = [
    os.path.join(cwd, "backend"),
    os.path.join(file_dir, "backend"),
    os.path.join(parent_dir, "backend"),
    cwd,
    file_dir,
    parent_dir
]

for p in path_candidates:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.main import app
except ImportError:
    try:
        from backend.app.main import app
    except Exception as err:
        print(f"Error importing app from backend: {err}")
        raise err
except Exception as err:
    print(f"Error importing app: {err}")
    raise err
