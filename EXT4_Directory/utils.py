#!/usr/bin/env python3
"""
Module: utils.py
Chức năng: Các hàm tiện ích chung
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from bitmap_recovery import BitmapRecovery


def check_bitmap_corruption(image_file):
    """
    Kiểm tra xem bitmaps có bị corrupt không (gần như toàn bộ = 0)
    Returns: True nếu corrupt, False nếu OK
    """
    if not os.path.exists(image_file):
        return False
    
    try:
        bitmap = BitmapRecovery(image_file)
        if not bitmap.load_filesystem_info():
            return False
        
        # Check block bitmap
        block_bitmap = bitmap.read_block_bitmap(0)
        block_non_zero = sum(1 for b in block_bitmap if b != 0)
        
        # Check inode bitmap  
        inode_bitmap = bitmap.read_inode_bitmap(0)
        inode_non_zero = sum(1 for b in inode_bitmap if b != 0)
        
        # Consider corrupted ONLY if nearly all zeros (< 0.01%)
        # Small filesystems may have only 0.1-5% non-zero bytes, which is normal
        block_corrupted = block_non_zero < len(block_bitmap) * 0.0001
        inode_corrupted = inode_non_zero < len(inode_bitmap) * 0.0001
        
        return block_corrupted or inode_corrupted
    except:
        return False


def check_filesystem_status(image_file):
    """
    Kiểm tra trạng thái tổng thể của filesystem
    Returns: True nếu OK, False nếu có vấn đề
    """
    if not os.path.exists(image_file):
        return False
    
    # First check if bitmaps are corrupted
    bitmap_corrupted = check_bitmap_corruption(image_file)
    if bitmap_corrupted:
        return False  # Bitmaps corrupted = not OK
    
    try:
        # Also try to mount to be sure
        loop_device = os.popen(f"losetup -f --show {image_file} 2>/dev/null").read().strip()
        if not loop_device:
            return False
        
        mount_point = "/tmp/check_fs_status"
        os.makedirs(mount_point, exist_ok=True)
        
        ret = os.system(f"mount {loop_device} {mount_point} 2>/dev/null")
        
        if ret == 0:
            os.system(f"umount {mount_point} 2>/dev/null")
            os.system(f"losetup -d {loop_device} 2>/dev/null")
            return True
        else:
            os.system(f"losetup -d {loop_device} 2>/dev/null")
            return False
    except:
        return False
