#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_utils import EXT4Utils
from ext4_structures import EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE


def check_and_display_filesystem(image_file, mount_point="/mnt/recovery_test"):
    
    if not os.path.exists(image_file):
        print(f" File khong ton tai: {image_file}")
        return False
    
    # Kiem tra quyen root
    if os.geteuid() != 0:
        print(" Canh bao: Can quyen root de mount filesystem!")
        print("  Chi co the phan tich metadata...")
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Kiem tra superblock co hop le khong
    print("\n Dang kiem tra superblock...")
    
    utils = EXT4Utils()
    data = utils.read_bytes(image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
    
    if not data:
        print(" Khong the doc superblock!")
        return False
    
    sb = utils.parse_superblock(data)
    
    if not sb or not sb.is_valid():
        print(" Superblock chinh BI HONG!")
        print(" Vui long chon option 3 de sua chua truoc.")
        return False
    
    print(" Superblock hop le!")
    
    # Hien thi thong tin co ban
    print(f"\n Thong tin filesystem:")
    print(f"   Block Size:        {sb.get_block_size()} bytes")
    print(f"   Total Blocks:      {sb.get_total_blocks():,}")
    print(f"   Total Inodes:      {sb.s_inodes_count:,}")
    print(f"   Free Blocks:       {sb.s_free_blocks_count_lo:,}")
    
    # Thu mount va doc du lieu
    if os.geteuid() == 0:
        print(f"\n Dang mount image vao {mount_point}...")
        os.makedirs(mount_point, exist_ok=True)
        
        ret = os.system(f"mount -o loop {image_file} {mount_point} 2>/dev/null")
        
        if ret == 0:
            print(" Mount thanh cong!")
            print(f"\n Noi dung filesystem:")
            os.system(f"ls -lah {mount_point} | head -20")
            
            # Doc test file neu co
            test_file = os.path.join(mount_point, "test_data.txt")
            if os.path.exists(test_file):
                print(f"\n Noi dung file test_data.txt:")
                with open(test_file, 'r') as f:
                    content = f.read().strip()
                    print(f"   >>> {content}")
            else:
                print(f"\n File test_data.txt khong ton tai")
            
            os.system(f"umount {mount_point} 2>/dev/null")
            print(f"\n Da unmount!")
            return True
        else:
            print(" Mount that bai!")
            return False
    else:
        print("\n Bo qua mount (can quyen root)")
        return True
