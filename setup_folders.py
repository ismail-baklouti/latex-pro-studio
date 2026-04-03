import os

def create_structure():
    folders = [
        "core",
        "ui",
        "utils",
        "citations",
        "assets/icons",
        "assets/img"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        # Create an empty __init__.py so Python treats folders as packages
        init_file = os.path.join(folder, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                pass
                
    print("✅ Latex Pro Studio folder structure created successfully!")
    print("Next step: Move your .py files into their respective folders.")

if __name__ == "__main__":
    create_structure()