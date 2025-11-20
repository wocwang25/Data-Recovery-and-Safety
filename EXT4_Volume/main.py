#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from volume_utils import check_superblock_valid, corrupt_superblock
from volume_checker import check_and_display_filesystem
from volume_recovery import recover_superblock


def print_banner():
    
    print("\n" + "=" * 70)
    print("\nCONG CU PHUC HOI DU LIEU EXT4 FILESYSTEM - Tham so sai cua Volume")
    print("\t\tData Recovery and Safety - HCMUS")
    print("=" * 70)
    print()


def print_menu(image_file, is_corrupted):
    
    os.system('clear')
    print_banner()
    print("\t\t\tMENU CHINH")
    print("-" * 70)
    
    if image_file:
        status = " BI HONG" if is_corrupted else " HOAT DONG"
        print(f" Image hien tai: {os.path.basename(image_file)} - Trang thai: {status}")
        print("-" * 70)
    
    print("1.  Kiem tra du lieu test image")
    print("2.  Pha hong superblock")
    print("3.  Sua chua/Phuc hoi superblock")
    print("0.  Thoat")
    print("-" * 70)


def handle_check_data(image_file):
    
    print("\n" + "=" * 70)
    print(" KIEM TRA DU LIEU TEST IMAGE")
    print("=" * 70)
    
    check_and_display_filesystem(image_file)


def handle_corrupt_superblock(image_file):
    
    print("\n" + "=" * 70)
    print(" PHA HONG SUPERBLOCK")
    print("=" * 70)
    
    # Confirm
    print("\n CANH BAO: Se ghi de superblock chinh bang du lieu rac!")
    print("  (Backup se duoc luu)")
    response = input("\n Ban co chac chan muon pha hong? (y/n): ").strip().lower()
    
    if response != 'y':
        print(" Da huy.")
        return False
    
    return corrupt_superblock(image_file)


def handle_recover_superblock(image_file):
    
    print("\n" + "=" * 70)
    print(" PHUC HOI SUPERBLOCK")
    print("=" * 70)
    
    # Buoc 1: Kiem tra superblock chinh
    print("\n" + "-" * 70)
    print("BUOC 1: Kiem tra superblock chinh")
    print("-" * 70)
    
    if check_superblock_valid(image_file):
        print(" Superblock chinh van con tot!")
        print("  Khong can phuc hoi.")
        return True
    else:
        print(" Superblock chinh bi hong!")
    
    return recover_superblock(image_file, auto_mode=False)


def main():
    
    print_banner()
    
    # Lay image file va auto mode tu arguments
    image_file = "test_image_1gb.img"
    auto_recover = False
    
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == "--auto-recover":
        auto_recover = True
    
    # Kiem tra file ton tai
    if not os.path.exists(image_file):
        print(f" File khong ton tai: {image_file}")
        if not auto_recover:
            print(" Script se su dung file nay khi duoc tao.")
        else:
            sys.exit(1)
    
    is_corrupted = not check_superblock_valid(image_file) if os.path.exists(image_file) else False
    
    # Neu auto mode, chi recover va thoat
    if auto_recover:
        if is_corrupted:
            print("\n Che do tu dong: Phuc hoi superblock...")
            if recover_superblock(image_file, auto_mode=True):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("\n Superblock da hoat dong binh thuong!")
            sys.exit(0)
    
    # Main loop
    while True:
        print_menu(image_file, is_corrupted)
        
        try:
            choice = input("\n Nhap lua chon cua ban: ").strip()
            
            if choice == '0':
                print("\n" + "=" * 70)
                print("\t\t\tCAM ON DA SU DUNG!")
                print("=" * 70)
                break
            
            elif choice == '1':
                # Kiem tra du lieu
                handle_check_data(image_file)
                # Cap nhat trang thai
                is_corrupted = not check_superblock_valid(image_file)
            
            elif choice == '2':
                # Pha hong
                if handle_corrupt_superblock(image_file):
                    is_corrupted = True
            
            elif choice == '3':
                # Sua chua
                if handle_recover_superblock(image_file):
                    is_corrupted = False
            
            else:
                print(" Lua chon khong hop le. Vui long chon 0-3.")
            
            try:
                input("\n Nhan Enter de tiep tuc...")
            except EOFError:
                pass
            print("\n" * 2)
            
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
                input("\n Nhan Enter de tiep tuc...")
            except EOFError:
                pass


if __name__ == "__main__":
    main()
