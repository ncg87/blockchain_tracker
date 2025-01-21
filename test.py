import sys
print("Python path:")
for p in sys.path:
    print(p)

print("\nTrying import...")
try:
    import python
    print("Success!")
    print("blockchain.__file__:", blockchain.__file__)
except ImportError as e:
    print("Import failed:", e)

print("\nChecking python directory...")
from pathlib import Path
python_dir = Path("python")
print("Contents:")
for item in python_dir.iterdir():
    print(f"  {item}")