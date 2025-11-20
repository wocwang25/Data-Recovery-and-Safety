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
    print("\nCONG CU PHUC HOI DU LIEU EXT4 FILESYSTEM - PARTITION TABLE EXT4")
    print("\t\tData Recovery and Safety - HCMUS")
    print("=" * 70)
    print()


def print_menu(disk_image, is_corrupted):
    
    os.system('clear')
    print_banner()
    print("\t\t\tMENU CHINH")
    print("-" * 70)
    
    if disk_image:
        status = " BI HONG" if is_corrupted else " HOAT DONG"
        print(f" Disk hien tai: {os.path.basename(disk_image)} - Partition Table: {status}")
        print("-" * 70)
    
    print("1.  Kiem tra partition table va du lieu")
    print("2.  Pha hong partition table")
    print("3.  Sua chua/Quet lai partitions")
    print("0.  Thoat")
    print("-" * 70)
