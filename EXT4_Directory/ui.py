#!/usr/bin/env python3

import os
import sys


def check_root():
    if os.geteuid() != 0:
        print("\n" + "=" * 70)
        print(" LOI: Chuong trinh nay can quyen root!")
        print("=" * 70)
        print("\n Vui long chay lai voi sudo:")
        print(f"   sudo python3 {sys.argv[0]}")
        print("")
        sys.exit(1)


def print_banner():
    print("\n" + "=" * 70)
    print("\n       CONG CU PHUC HOI DIRECTORY VA BITMAP EXT4")
    print("       Data Recovery and Safety - HCMUS")
    print("=" * 70)
    print()


def print_menu(image_file, is_corrupted, file_exists=True):
    os.system('clear')
    print_banner()
    print("\t\t\tMENU CHINH")
    print("-" * 70)
    
    if file_exists:
        if image_file:
            status = "❌ BI HONG" if is_corrupted else "✅ HOAT DONG"
            size_mb = os.path.getsize(image_file) / (1024**2)
            print(f" Image: {os.path.basename(image_file)} ({size_mb:.1f} MB)")
            print(f" Trang thai: {status}")
            print("-" * 70)
    else:
        print(f" Image: {os.path.basename(image_file) if image_file else 'N/A'}")
        print(f" Trang thai: ⚠️  CHUA TON TAI")
        print("-" * 70)
    
    print("1.  Kiem tra du lieu image")
    print("2.  Pha hong directory/bitmap")
    print("3.  Phuc hoi directory/bitmap")
    print("4.  Xem thong tin chi tiet")
    print("0.  Thoat")
    print("-" * 70)
