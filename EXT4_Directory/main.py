#!/usr/bin/env python3
"""
Main program: EXT4 Directory & Bitmap Recovery
"""

import sys
import os

from handlers import (
    handle_check_data,
    handle_corrupt_data,
    handle_recover_data,
    handle_show_details
)
from utils import check_filesystem_status
from ui import check_root, print_menu


def main():
    """Main entry point"""
    check_root()
    
    # Lay image file tu argument hoac dung mac dinh
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
    else:
        image_file = "test_directory.img"
    
    file_exists = os.path.exists(image_file)
    
    # Kiem tra trang thai filesystem
    is_corrupted = not check_filesystem_status(image_file) if file_exists else False
    scanner = None
    
    while True:
        print_menu(image_file, is_corrupted, file_exists)
        
        try:
            choice = input("\n📝 Nhap lua chon cua ban: ").strip()
            
            if choice == '0':
                print("\n" + "=" * 70)
                print("👋 CAM ON DA SU DUNG!")
                print("=" * 70)
                break
            
            elif choice == '1':
                # Kiem tra du lieu
                handle_check_data(image_file)
                file_exists = os.path.exists(image_file)
                is_corrupted = not check_filesystem_status(image_file) if file_exists else False
            
            elif choice == '2':
                # Pha hong
                if handle_corrupt_data(image_file):
                    is_corrupted = True
            
            elif choice == '3':
                # Phuc hoi
                scanner = handle_recover_data(image_file)
                if scanner:
                    is_corrupted = not check_filesystem_status(image_file)
            
            elif choice == '4':
                # Xem thong tin chi tiet
                handle_show_details(image_file)
            
            else:
                print("\n❌ Lua chon khong hop le. Vui long chon 0-4.")
            
            try:
                input("\n⏎  Nhan Enter de tiep tuc...")
            except EOFError:
                pass
            
        except KeyboardInterrupt:
            print("\n\n👋 Tam biet!")
            break
        except EOFError:
            print("\n\n👋 Tam biet!")
            break
        except Exception as e:
            print(f"\n❌ Loi: {e}")
            import traceback
            traceback.print_exc()
            try:
                input("\n⏎  Nhan Enter de tiep tuc...")
            except EOFError:
                pass


if __name__ == "__main__":
    main()
