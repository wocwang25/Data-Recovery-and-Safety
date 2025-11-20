#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))

from ui import check_root, print_banner, print_menu
from partition_utils import check_partition_table_valid
from partition_handlers import handle_check_data, handle_corrupt_partition_table, handle_scan_and_recover





def main():
    check_root()
    print_banner()
    
    # Lay disk image tu argument hoac dung mac dinh
    if len(sys.argv) > 1:
        disk_image = sys.argv[1]
    else:
        disk_image = "test_disk_multipart.img"
    
    # Kiem tra file ton tai
    if not os.path.exists(disk_image):
        print(f" File khong ton tai: {disk_image}")
        print(" Script se su dung file nay khi duoc tao.")
    
    is_corrupted = not check_partition_table_valid(disk_image) if os.path.exists(disk_image) else False
    scanner = None
    
    while True:
        print_menu(disk_image, is_corrupted)
        
        try:
            choice = input("\n Nhap lua chon cua ban: ").strip()
            
            if choice == '0':
                print("\n" + "=" * 70)
                print(" CAM ON DA SU DUNG!")
                print("=" * 70)
                break
            
            elif choice == '1':
                # Kiem tra du lieu
                handle_check_data(disk_image)
                # Cap nhat trang thai
                is_corrupted = not check_partition_table_valid(disk_image)
            
            elif choice == '2':
                # Pha hong
                if handle_corrupt_partition_table(disk_image):
                    is_corrupted = True
            
            elif choice == '3':
                # Sua chua
                scanner = handle_scan_and_recover(disk_image)
                if scanner:
                    is_corrupted = False
            
            else:
                print("Loi: Lua chon khong hop le. Vui long chon 0-3.")
            
            try:
                input("\n  Nhan Enter de tiep tuc...")
            except EOFError:
                pass
            
        except KeyboardInterrupt:
            print("\n\n Tam biet!")
            break
        except EOFError:
            print("\n\n Tam biet!")
            break
        except Exception as e:
            print(f"\n Loi: {e}")
            import traceback
            traceback.print_exc()
            try:
                input("\n  Nhan Enter de tiep tuc...")
            except EOFError:
                pass


if __name__ == "__main__":
    main()
