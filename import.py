import os
import shutil
from datetime import datetime

def import_pictures():
    week_number = datetime.now().isocalendar()[1]
    input_dir = 'input'
    output_dir = os.path.join('static', 'pictures', str(week_number))

    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith(('.jpeg', '.jpg'))]

    if not files:
        print(f"No JPEG files found in '{input_dir}'.")
        return

    os.makedirs(output_dir, exist_ok=True)

    for filename in files:
        source_path = os.path.join(input_dir, filename)
        destination_path = os.path.join(output_dir, filename)
        try:
            shutil.move(source_path, destination_path)
            print(f"Moved '{filename}' to '{output_dir}'")
        except Exception as e:
            print(f"Error moving '{filename}': {e}")

if __name__ == "__main__":
    import_pictures()
