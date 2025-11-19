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
        
        # Danh dau cac block metadata cho moi group
        print(" Dang danh dau metadata blocks...")
        for group_num in range(num_groups):
            gd = self.group_descriptors[group_num]
            
            # 1. Superblock (chi group 0 hoac sparse groups)
            if group_num == 0:
                # Block 0 (boot block) va block 1 (superblock)
                for block_idx in range(2):
                    self._mark_block_used(new_bitmaps, group_num, block_idx, blocks_per_group)
            
            # 2. Group Descriptor Table
            # GDT bat dau sau superblock
            gdt_start = 2 if group_num == 0 else 0
            gdt_blocks = (num_groups * 32 + block_size - 1) // block_size
            for i in range(gdt_blocks):
                self._mark_block_used(new_bitmaps, group_num, gdt_start + i, blocks_per_group)
            
            # 3. Reserved GDT blocks (cho future resize)
            reserved_gdt = self.superblock.s_reserved_gdt_blocks
            for i in range(reserved_gdt):
                self._mark_block_used(new_bitmaps, group_num, gdt_start + gdt_blocks + i, blocks_per_group)
            
            # 4. Block bitmap
            block_bitmap_block = gd.bg_block_bitmap_lo
            self._mark_block_used_absolute(new_bitmaps, block_bitmap_block, blocks_per_group)
            
            # 5. Inode bitmap
            inode_bitmap_block = gd.bg_inode_bitmap_lo
            self._mark_block_used_absolute(new_bitmaps, inode_bitmap_block, blocks_per_group)
            
            # 6. Inode table
            inode_table_block = gd.bg_inode_table_lo
            inodes_per_group = self.superblock.s_inodes_per_group
            inode_size = self.superblock.s_inode_size
            inode_table_blocks = (inodes_per_group * inode_size + block_size - 1) // block_size
            
            for i in range(inode_table_blocks):
                self._mark_block_used_absolute(new_bitmaps, inode_table_block + i, blocks_per_group)
        
        # Danh dau journal blocks (inode 8)
        print(" Dang danh dau journal blocks...")
        journal_inode = None
        for inode_info in inodes_data:
            if inode_info['inode_num'] == 8:  # Journal inode
                journal_inode = inode_info['inode']
                break
        
        if journal_inode:
            self._mark_inode_blocks(new_bitmaps, journal_inode, blocks_per_group)
        
        # Danh dau blocks duoc su dung boi data files
        print(" Dang danh dau data blocks...")
        for inode_info in inodes_data:
            inode = inode_info['inode']
            self._mark_inode_blocks(new_bitmaps, inode, blocks_per_group)
        
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
    
    def _mark_block_used_absolute(self, bitmaps, absolute_block, blocks_per_group):
        """Mark a block as used given its absolute block number"""
        group_num = absolute_block // blocks_per_group
        local_block = absolute_block % blocks_per_group
        
        if group_num >= len(bitmaps):
            return
        
        byte_idx = local_block // 8
        bit_idx = local_block % 8
        
        if byte_idx < len(bitmaps[group_num]):
            bitmaps[group_num][byte_idx] |= (1 << bit_idx)
    
    def _mark_block_used(self, bitmaps, group_num, local_block, blocks_per_group):
        
        if group_num >= len(bitmaps):
            return
        
        if local_block >= blocks_per_group:
            return
        
        byte_idx = local_block // 8
        bit_idx = local_block % 8
        
        if byte_idx < len(bitmaps[group_num]):
            bitmaps[group_num][byte_idx] |= (1 << bit_idx)
    
    def _mark_inode_blocks(self, bitmaps, inode, blocks_per_group):
        
        if not inode:
            return
        
        # i_block is a tuple of 15 integers (4 bytes each)
        # Pack it into bytes for parsing
        i_block_bytes = b''
        for val in inode.i_block:
            i_block_bytes += val.to_bytes(4, 'little')
        
        # Parse extent tree de lay block numbers
        if inode.i_flags & 0x80000:  # EXT4_EXTENTS_FL
            extent_header_data = i_block_bytes[:12]
            
            if len(extent_header_data) < 12:
                return
            
            # Check magic
            try:
                eh_magic = int.from_bytes(extent_header_data[0:2], 'little')
            except:
                return
                
            if eh_magic != 0xF30A:
                return
            
            eh_entries = int.from_bytes(extent_header_data[2:4], 'little')
            eh_depth = int.from_bytes(extent_header_data[6:8], 'little')
            
            if eh_depth == 0:  # Leaf node
                # Parse extent entries
                for i in range(min(eh_entries, 4)):  # Max 4 extents in inode
                    extent_offset = 12 + i * 12
                    if extent_offset + 12 <= len(i_block_bytes):
                        extent_data = i_block_bytes[extent_offset:extent_offset+12]
                        
                        ee_len = int.from_bytes(extent_data[4:6], 'little')
                        ee_start_hi = int.from_bytes(extent_data[6:8], 'little')
                        ee_start_lo = int.from_bytes(extent_data[8:12], 'little')
                        
                        physical_block = (ee_start_hi << 32) | ee_start_lo
                        
                        # Danh dau cac blocks
                        for block_num in range(physical_block, physical_block + ee_len):
                            self._mark_block_used_absolute(bitmaps, block_num, blocks_per_group)
            else:
                # Internal node - would need to follow extent index
                # For now, just mark the extent tree blocks themselves
                for i in range(min(eh_entries, 4)):
                    extent_offset = 12 + i * 12
                    if extent_offset + 12 <= len(i_block_bytes):
                        extent_data = i_block_bytes[extent_offset:extent_offset+12]
                        
                        # ei_leaf points to next level
                        ei_leaf_lo = int.from_bytes(extent_data[4:8], 'little')
                        ei_leaf_hi = int.from_bytes(extent_data[8:10], 'little')
                        leaf_block = (ei_leaf_hi << 32) | ei_leaf_lo
                        
                        self._mark_block_used_absolute(bitmaps, leaf_block, blocks_per_group)
        else:
            # Direct/indirect block pointers (old style)
            # Direct blocks (0-11)
            for i in range(12):
                if i < len(inode.i_block):
                    block_num = inode.i_block[i]
                    if block_num > 0:
                        self._mark_block_used_absolute(bitmaps, block_num, blocks_per_group)
            
            # Indirect block (12)
            if 12 < len(inode.i_block):
                indirect_block = inode.i_block[12]
                if indirect_block > 0:
                    self._mark_block_used_absolute(bitmaps, indirect_block, blocks_per_group)
            
            # Double indirect (13) and Triple indirect (14)
            for i in [13, 14]:
                if i < len(inode.i_block):
                    block_num = inode.i_block[i]
                    if block_num > 0:
                        self._mark_block_used_absolute(bitmaps, block_num, blocks_per_group)
