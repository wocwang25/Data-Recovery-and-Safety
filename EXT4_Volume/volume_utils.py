#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_utils import EXT4Utils
from ext4_structures import EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE


def check_superblock_valid(image_file):
    
    utils = EXT4Utils()
    data = utils.read_bytes(image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
    if not data:
        return False
    
    sb = utils.parse_superblock(data)
    return sb and sb.is_valid()


def corrupt_superblock(image_file):
    
    if not os.path.exists(image_file):
        print(f" Loi: File khong ton tai: {image_file}")
        return False
    
    # Kiem tra truoc
    if not check_superblock_valid(image_file):
        print(" Superblock da bi hong tu truoc!")
        return False
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Backup truoc khi pha
    backup_file = image_file + ".backup"
    print(f"\n Dang tao backup -> {backup_file}")
    
    try:
        import shutil
        shutil.copy2(image_file, backup_file)
        print(" Backup thanh cong!")
    except Exception as e:
        print(f" Loi khi backup: {e}")
        return False
    
    # Pha hong bang cach ghi 0 vao superblock
    print("\n Dang ghi de superblock tai offset 1024...")
    
    try:
        with open(image_file, 'r+b') as f:
            f.seek(1024)
            f.write(b'\x00' * 100)  # Ghi 100 bytes 0
        
        print(" Da pha hong superblock!")
        
        # Verify
        if not check_superblock_valid(image_file):
            print(" Xac nhan: Superblock da bi hong!")
            print(f"\n De restore: cp {backup_file} {image_file}")
            return True
        else:
            print(" La! Superblock van con hop le?")
            return False
            
    except Exception as e:
        print(f" Loi: {e}")
        return False


def find_backup_superblock(image_file):
    
    utils = EXT4Utils()
    
    backup_sb_data = None
    block_size_found = None
    backup_offset = None
    backup_group = None
    
    for block_size in [4096, 2048, 1024]:
        print(f"\n  Thu block size = {block_size} bytes...")
        blocks_per_group = 8 * block_size
        
        for group_num in [1, 3, 5, 7, 9]:
            group_start_block = group_num * blocks_per_group
            
            if block_size == 1024:
                offset = group_start_block * block_size + 1024
            else:
                offset = group_start_block * block_size
            
            try:
                file_size = os.path.getsize(image_file)
                if offset + 1024 > file_size:
                    continue
            except:
                continue
            
            data = utils.read_bytes(image_file, offset, 1024)
            if data:
                sb = utils.parse_superblock(data)
                if sb and sb.is_valid():
                    backup_sb_data = data
                    block_size_found = block_size
                    backup_offset = offset
                    backup_group = group_num
                    print(f"   Tim thay backup tai group {group_num} (offset: {offset})")
                    break
        
        if backup_sb_data:
            break
    
    if backup_sb_data:
        return {
            'data': backup_sb_data,
            'block_size': block_size_found,
            'offset': backup_offset,
            'group': backup_group
        }
    
    return None


def restore_superblock_from_backup(image_file, backup_data):
    
    # Backup truoc khi sua
    backup_file = image_file + ".before_recovery"
    print(f"\n Dang backup file goc -> {backup_file}")
    
    try:
        import shutil
        shutil.copy2(image_file, backup_file)
        print(" Da backup!")
    except Exception as e:
        print(f" Khong the backup: {e}")
        return False
    
    # Ghi de superblock
    print("\n Dang ghi superblock...")
    
    try:
        with open(image_file, 'r+b') as f:
            f.seek(1024)
            f.write(backup_data)
        
        return True
        
    except Exception as e:
        print(f"\n Phuc hoi that bai: {e}")
        return False
