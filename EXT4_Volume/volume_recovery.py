#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from volume_utils import find_backup_superblock, restore_superblock_from_backup


def recover_superblock(image_file, auto_mode=False):
    
    if not os.path.exists(image_file):
        print(f" File khong ton tai: {image_file}")
        return False
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Buoc 2: Tim backup
    print("\n" + "-" * 70)
    print("BUOC 2: Tim backup superblock")
    print("-" * 70)
    
    backup_info = find_backup_superblock(image_file)
    
    if not backup_info:
        print("\n Khong tim thay backup superblock nao!")
        return False
    
    # Buoc 3: Khoi phuc
    print("\n" + "-" * 70)
    print("BUOC 3: Khoi phuc superblock chinh")
    print("-" * 70)
    
    print(f"\n Chuan bi ghi de superblock chinh bang backup...")
    print(f"   Block size phat hien: {backup_info['block_size']} bytes")
    print(f"   Backup group: {backup_info['group']}")
    print(f"   Backup offset: {backup_info['offset']}")
    
    if not auto_mode:
        response = input("\n Ban co muon tiep tuc? (y/n): ").strip().lower()
        
        if response != 'y':
            print(" Da huy.")
            return False
    else:
        print("\n Che do tu dong: Tien hanh phuc hoi...")
    
    # Ghi de superblock
    if restore_superblock_from_backup(image_file, backup_info['data']):
        print("\n" + "=" * 70)
        print(" PHUC HOI THANH CONG! ")
        print("=" * 70)
        print(f"\n File da duoc sua: {image_file}")
        print(f" Backup goc: {image_file}.backup_volume")
        print("\n Filesystem da duoc khoi phuc!")
        print("=" * 70)
        return True
    else:
        return False
