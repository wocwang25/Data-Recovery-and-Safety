import sys
import os

from ui import check_root, print_menu, get_menu_choice
from handlers import (
    handle_check_data,
    handle_delete_data,
    handle_recover_data
)


def main():
    # Check arguments
    if len(sys.argv) < 2:
        # Tìm .img files trong thư mục hiện tại
        current_dir = os.path.dirname(os.path.abspath(__file__))
        img_files = [f for f in os.listdir(current_dir) if f.endswith('.img')]
        
        if img_files:
            print("Found image files in current directory:")
            for i, f in enumerate(img_files, 1):
                size_mb = os.path.getsize(os.path.join(current_dir, f)) / 1024**2
                print(f"  {i}. {f} ({size_mb:.1f} MB)")
            
            try:
                choice = input(f"\nSelect image [1-{len(img_files)}] or 0 to exit: ").strip()
                if choice == '0':
                    sys.exit(0)
                idx = int(choice) - 1
                if 0 <= idx < len(img_files):
                    image_file = os.path.join(current_dir, img_files[idx])
                else:
                    print("✗ Invalid selection!")
                    sys.exit(1)
            except (ValueError, KeyboardInterrupt):
                print("\n✗ Invalid input!")
                sys.exit(1)
        else:
            print("Usage: sudo python3 main.py <image_file>")
            print("\nExample:")
            print("  sudo python3 main.py /dev/sdb1")
            print("  sudo python3 main.py disk.img")
            print("\nOr place .img file in current directory and run without arguments")
            sys.exit(1)
    else:
        image_file = sys.argv[1]
        
        # Nếu không phải absolute path, tìm trong current directory
        if not os.path.isabs(image_file):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            image_file = os.path.join(current_dir, image_file)
    
    # Check if image exists
    if not os.path.exists(image_file):
        print(f"✗ Image file not found: {image_file}")
        sys.exit(1)
    
    # Check root
    check_root()
    
    # Welcome
    print("=" * 70)
    print("EXT4 FILE CARVING - Deleted File Recovery")
    print("=" * 70)
    print(f"Image: {image_file}")
    print(f"Size: {os.path.getsize(image_file) / 1024**2:.1f} MB")
    
    # Main loop
    while True:
        print_menu()
        choice = get_menu_choice()
        
        if choice == '1':
            handle_check_data(image_file)
        elif choice == '2':
            handle_delete_data(image_file)
        elif choice == '3':
            handle_recover_data(image_file)
        elif choice == '0':
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid option! Please select 0-3")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
