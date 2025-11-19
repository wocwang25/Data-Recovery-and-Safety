#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_structures import (
    Superblock, GroupDescriptor, Inode, DirectoryEntry,
    EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE,
    EXT4_GROUP_DESC_SIZE
)
from ext4_utils import EXT4Utils


class BitmapRecovery:
    
    def __init__(self, image_file):
        self.image_file = image_file
        self.utils = EXT4Utils()
        self.superblock = None
        self.group_descriptors = []
        
    def load_filesystem_info(self):
        
        # Doc superblock
        sb_data = self.utils.read_bytes(self.image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
        if not sb_data:
            print("   Loi: Khong doc duoc superblock data")
            return False
            
        self.superblock = self.utils.parse_superblock(sb_data)
        if not self.superblock:
            print("   Loi: Khong parse duoc superblock")
            return False
        
        if not self.superblock.is_valid():
            print(f"   Canh bao: Superblock khong hop le (magic = 0x{self.superblock.s_magic:X})")
            print("   Tiep tuc thu doc group descriptors...")
        
        # Doc group descriptors
        try:
            block_size = self.superblock.get_block_size()
            gdt_block = 1 if block_size == 1024 else 0
            gdt_offset = (gdt_block + 1) * block_size
            
            num_groups = (self.superblock.s_blocks_count_lo + self.superblock.s_blocks_per_group - 1) // self.superblock.s_blocks_per_group
            
            for i in range(num_groups):
                offset = gdt_offset + i * EXT4_GROUP_DESC_SIZE
                gd_data = self.utils.read_bytes(self.image_file, offset, EXT4_GROUP_DESC_SIZE)
                
                if gd_data:
                    gd = self.utils.parse_group_descriptor(gd_data)
                    if gd:
                        self.group_descriptors.append(gd)
            
            return True
        except Exception as e:
            print(f"   Loi khi doc group descriptors: {e}")
            return False
    
    def get_block_bitmap_info(self, group_num):
        
        if group_num >= len(self.group_descriptors):
            return None
        
        gd = self.group_descriptors[group_num]
        block_size = self.superblock.get_block_size()
        
        bitmap_block = gd.bg_block_bitmap_lo
        bitmap_offset = bitmap_block * block_size
        
        return {
            'group': group_num,
            'bitmap_block': bitmap_block,
            'bitmap_offset': bitmap_offset,
            'size': block_size
        }
    
    def get_inode_bitmap_info(self, group_num):
        
        if group_num >= len(self.group_descriptors):
            return None
        
        gd = self.group_descriptors[group_num]
        block_size = self.superblock.get_block_size()
        
        bitmap_block = gd.bg_inode_bitmap_lo
        bitmap_offset = bitmap_block * block_size
        
        return {
            'group': group_num,
            'bitmap_block': bitmap_block,
            'bitmap_offset': bitmap_offset,
            'size': block_size
        }
    
    def read_block_bitmap(self, group_num):
        
        info = self.get_block_bitmap_info(group_num)
        if not info:
            return None
        
        return self.utils.read_bytes(self.image_file, info['bitmap_offset'], info['size'])
    
    def read_inode_bitmap(self, group_num):
        
        info = self.get_inode_bitmap_info(group_num)
        if not info:
            return None
        
        return self.utils.read_bytes(self.image_file, info['bitmap_offset'], info['size'])
    
    def corrupt_block_bitmap(self, group_num):
        
        info = self.get_block_bitmap_info(group_num)
        if not info:
            return False
        
        print(f"\n Dang pha hong block bitmap cua group {group_num}...")
        print(f"   Offset: {info['bitmap_offset']}")
        print(f"   Size: {info['size']} bytes")
        
        # Backup
        backup_file = self.image_file + f".backup_block_bitmap_g{group_num}"
        bitmap_data = self.read_block_bitmap(group_num)
        
        if bitmap_data:
            with open(backup_file, 'wb') as f:
                f.write(bitmap_data)
            print(f"   Backup -> {backup_file}")
        
        # Ghi de bang zeros
        try:
            with open(self.image_file, 'r+b') as f:
                f.seek(info['bitmap_offset'])
                f.write(b'\x00' * info['size'])
            
            print(" Da pha hong block bitmap!")
            return True
        except Exception as e:
            print(f" Loi: {e}")
            return False
    
    def corrupt_inode_bitmap(self, group_num):
        
        info = self.get_inode_bitmap_info(group_num)
        if not info:
            return False
        
        print(f"\n Dang pha hong inode bitmap cua group {group_num}...")
        print(f"   Offset: {info['bitmap_offset']}")
        print(f"   Size: {info['size']} bytes")
        
        # Backup
        backup_file = self.image_file + f".backup_inode_bitmap_g{group_num}"
        bitmap_data = self.read_inode_bitmap(group_num)
        
        if bitmap_data:
            with open(backup_file, 'wb') as f:
                f.write(bitmap_data)
            print(f"   Backup -> {backup_file}")
        
        # Ghi de bang zeros
        try:
            with open(self.image_file, 'r+b') as f:
                f.seek(info['bitmap_offset'])
                f.write(b'\x00' * info['size'])
            
            print(" Da pha hong inode bitmap!")
            return True
        except Exception as e:
            print(f" Loi: {e}")
            return False
    
    def rebuild_block_bitmap_from_inodes(self, inodes_data):
        
        print("\n Dang xay dung lai block bitmap tu inode data...")
        
        if not self.superblock:
            return False
        
        block_size = self.superblock.get_block_size()
        blocks_per_group = self.superblock.s_blocks_per_group
        num_groups = len(self.group_descriptors)
        
        # Tao bitmap moi (tat ca = 0 = free)
        new_bitmaps = []
        for _ in range(num_groups):
            bitmap_size = blocks_per_group // 8
            new_bitmaps.append(bytearray(bitmap_size))
        
        # Danh dau cac block metadata (superblock, gdt, bitmaps, inode table)
        for group_num in range(num_groups):
            # Simplified - chi danh dau metadata blocks
            # Block 0-31: superblock + GDT + bitmaps + inode table start
            for block_idx in range(32):
                byte_idx = block_idx // 8
                bit_idx = block_idx % 8
                if byte_idx < len(new_bitmaps[group_num]):
                    new_bitmaps[group_num][byte_idx] |= (1 << bit_idx)
        
        # Danh dau blocks duoc su dung boi inodes
        for inode_info in inodes_data:
            inode = inode_info['inode']
            
            # Parse extent tree de lay block numbers
            # Simplified version
            if inode.i_flags & 0x80000:  # EXT4_EXTENTS_FL
                extent_header_data = inode.i_block[:12]
                num_extents = extent_header_data[2]
                
                for i in range(min(num_extents, 4)):
                    extent_offset = 12 + i * 12
                    if extent_offset + 12 <= len(inode.i_block):
                        extent_data = inode.i_block[extent_offset:extent_offset+12]
                        
                        ee_len = int.from_bytes(extent_data[4:6], 'little')
                        ee_start_hi = int.from_bytes(extent_data[6:8], 'little')
                        ee_start_lo = int.from_bytes(extent_data[8:12], 'little')
                        
                        physical_block = (ee_start_hi << 32) | ee_start_lo
                        
                        # Danh dau cac blocks
                        for block_num in range(physical_block, physical_block + ee_len):
                            group_num = block_num // blocks_per_group
                            local_block = block_num % blocks_per_group
                            
                            if group_num < num_groups:
                                byte_idx = local_block // 8
                                bit_idx = local_block % 8
                                
                                if byte_idx < len(new_bitmaps[group_num]):
                                    new_bitmaps[group_num][byte_idx] |= (1 << bit_idx)
        
        # Ghi lai block bitmaps
        print(" Dang ghi lai block bitmaps...")
        for group_num in range(num_groups):
            info = self.get_block_bitmap_info(group_num)
            if info:
                try:
                    with open(self.image_file, 'r+b') as f:
                        f.seek(info['bitmap_offset'])
                        f.write(bytes(new_bitmaps[group_num]))
                    print(f"   Group {group_num}: OK")
                except Exception as e:
                    print(f"   Group {group_num}: Loi - {e}")
        
        print(" Hoan thanh rebuild block bitmap!")
        return True
    
    def rebuild_inode_bitmap_from_scan(self, inodes_data):
        
        print("\n Dang xay dung lai inode bitmap tu inode scan...")
        
        if not self.superblock:
            return False
        
        inodes_per_group = self.superblock.s_inodes_per_group
        num_groups = len(self.group_descriptors)
        
        # Tao bitmap moi
        new_bitmaps = []
        for _ in range(num_groups):
            bitmap_size = inodes_per_group // 8
            new_bitmaps.append(bytearray(bitmap_size))
        
        # Danh dau cac inode dang su dung
        for inode_info in inodes_data:
            inode_num = inode_info['inode_num']
            
            group_num = (inode_num - 1) // inodes_per_group
            local_inode = (inode_num - 1) % inodes_per_group
            
            if group_num < num_groups:
                byte_idx = local_inode // 8
                bit_idx = local_inode % 8
                
                if byte_idx < len(new_bitmaps[group_num]):
                    new_bitmaps[group_num][byte_idx] |= (1 << bit_idx)
        
        # Ghi lai inode bitmaps
        print(" Dang ghi lai inode bitmaps...")
        for group_num in range(num_groups):
            info = self.get_inode_bitmap_info(group_num)
            if info:
                try:
                    with open(self.image_file, 'r+b') as f:
                        f.seek(info['bitmap_offset'])
                        f.write(bytes(new_bitmaps[group_num]))
                    print(f"   Group {group_num}: OK")
                except Exception as e:
                    print(f"   Group {group_num}: Loi - {e}")
        
        print(" Hoan thanh rebuild inode bitmap!")
        return True
