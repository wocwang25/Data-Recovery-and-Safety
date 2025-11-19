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


class DirectoryScanner:
    
    def __init__(self, image_file):
        self.image_file = image_file
        self.utils = EXT4Utils()
        self.superblock = None
        self.group_descriptors = []
        self.found_inodes = []
        self.directory_tree = {}
        
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
            # Khong return False, van thu tiep
        
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
    
    def read_inode(self, inode_num):
        
        if not self.superblock or not self.group_descriptors:
            return None
        
        # Tinh group va index
        group_num = (inode_num - 1) // self.superblock.s_inodes_per_group
        local_index = (inode_num - 1) % self.superblock.s_inodes_per_group
        
        if group_num >= len(self.group_descriptors):
            return None
        
        # Lay inode table offset
        gd = self.group_descriptors[group_num]
        inode_table_block = gd.bg_inode_table_lo
        
        block_size = self.superblock.get_block_size()
        inode_size = self.superblock.s_inode_size
        
        inode_offset = inode_table_block * block_size + local_index * inode_size
        
        # Doc inode
        inode_data = self.utils.read_bytes(self.image_file, inode_offset, inode_size)
        if not inode_data:
            return None
        
        return self.utils.parse_inode(inode_data)
    
    def read_directory_entries(self, inode_num):
        
        inode = self.read_inode(inode_num)
        if not inode or not inode.is_directory():
            return []
        
        entries = []
        block_size = self.superblock.get_block_size()
        
        # Doc extent header
        extent_header_data = inode.i_block[:12]
        
        # Simple case: direct blocks in i_block
        # Gia su su dung extent tree
        if inode.i_flags & 0x80000:  # EXT4_EXTENTS_FL
            # Parse extent tree (simplified)
            # Chi xu ly extent leaf nodes
            num_extents = extent_header_data[2]  # eh_entries
            
            for i in range(min(num_extents, 4)):  # Goi han 4 extents
                extent_offset = 12 + i * 12
                if extent_offset + 12 <= len(inode.i_block):
                    extent_data = inode.i_block[extent_offset:extent_offset+12]
                    
                    # Parse extent entry
                    ee_block = int.from_bytes(extent_data[0:4], 'little')
                    ee_len = int.from_bytes(extent_data[4:6], 'little')
                    ee_start_hi = int.from_bytes(extent_data[6:8], 'little')
                    ee_start_lo = int.from_bytes(extent_data[8:12], 'little')
                    
                    physical_block = (ee_start_hi << 32) | ee_start_lo
                    
                    # Doc data block
                    for block_idx in range(ee_len):
                        data_offset = (physical_block + block_idx) * block_size
                        block_data = self.utils.read_bytes(self.image_file, data_offset, block_size)
                        
                        if block_data:
                            entries.extend(self.parse_directory_block(block_data))
        else:
            # Direct blocks
            for i in range(12):
                block_num = int.from_bytes(inode.i_block[i*4:(i+1)*4], 'little')
                if block_num == 0:
                    break
                
                data_offset = block_num * block_size
                block_data = self.utils.read_bytes(self.image_file, data_offset, block_size)
                
                if block_data:
                    entries.extend(self.parse_directory_block(block_data))
        
        return entries
    
    def parse_directory_block(self, block_data):
        
        entries = []
        offset = 0
        
        while offset < len(block_data):
            if offset + 8 > len(block_data):
                break
            
            inode = int.from_bytes(block_data[offset:offset+4], 'little')
            rec_len = int.from_bytes(block_data[offset+4:offset+6], 'little')
            name_len = block_data[offset+6]
            file_type = block_data[offset+7]
            
            if rec_len == 0 or rec_len > len(block_data) - offset:
                break
            
            if inode != 0 and name_len > 0:
                name = block_data[offset+8:offset+8+name_len].decode('utf-8', errors='ignore')
                
                entries.append({
                    'inode': inode,
                    'name': name,
                    'file_type': file_type
                })
            
            offset += rec_len
        
        return entries
    
    def scan_all_inodes(self):
        
        if not self.superblock:
            return False
        
        print(" Dang quet tat ca inodes...")
        
        total_inodes = self.superblock.s_inodes_count
        self.found_inodes = []
        
        for inode_num in range(1, total_inodes + 1):
            # Skip reserved inodes
            if inode_num < 11 and inode_num not in [2, 8]:  # Root=2, Journal=8
                continue
            
            inode = self.read_inode(inode_num)
            
            if inode and inode.i_mode != 0:
                self.found_inodes.append({
                    'inode_num': inode_num,
                    'inode': inode,
                    'is_dir': inode.is_directory(),
                    'is_file': inode.is_regular_file(),
                    'size': inode.get_size()
                })
            
            # Progress
            if inode_num % 1000 == 0:
                print(f"   Scanned {inode_num}/{total_inodes} inodes...", end='\r')
        
        print(f"\n Tim thay {len(self.found_inodes)} inodes hop le!")
        return True
    
    def rebuild_directory_tree(self):
        
        if not self.found_inodes:
            return False
        
        print("\n Dang xay dung lai cay thu muc...")
        
        self.directory_tree = {}
        
        # Bat dau tu root (inode 2)
        root_entries = self.read_directory_entries(2)
        
        if root_entries:
            self.directory_tree[2] = {
                'path': '/',
                'entries': root_entries,
                'parent': 0
            }
            
            print(f"   Root directory: {len(root_entries)} entries")
            
            # Recursively scan subdirectories
            self._scan_directory_recursive(2, '/')
        
        return True
    
    def _scan_directory_recursive(self, inode_num, current_path, max_depth=10):
        
        if max_depth <= 0:
            return
        
        if inode_num not in self.directory_tree:
            return
        
        entries = self.directory_tree[inode_num]['entries']
        
        for entry in entries:
            if entry['name'] in ['.', '..']:
                continue
            
            if entry['file_type'] == 2:  # Directory
                subdir_path = os.path.join(current_path, entry['name'])
                subdir_inode = entry['inode']
                
                subdir_entries = self.read_directory_entries(subdir_inode)
                
                if subdir_entries:
                    self.directory_tree[subdir_inode] = {
                        'path': subdir_path,
                        'entries': subdir_entries,
                        'parent': inode_num
                    }
                    
                    # Recursive
                    self._scan_directory_recursive(subdir_inode, subdir_path, max_depth - 1)
    
    def print_directory_tree(self):
        
        print("\n" + "=" * 70)
        print(" CAY THU MUC")
        print("=" * 70)
        
        if not self.directory_tree:
            print(" Chua co du lieu!")
            return
        
        # In theo thu tu path
        sorted_dirs = sorted(self.directory_tree.items(), key=lambda x: x[1]['path'])
        
        for inode_num, dir_info in sorted_dirs:
            path = dir_info['path']
            entries = dir_info['entries']
            
            print(f"\n{path} (inode {inode_num}):")
            
            for entry in entries:
                if entry['name'] in ['.', '..']:
                    continue
                
                type_name = {
                    1: '[FILE]',
                    2: '[DIR] ',
                    7: '[LINK]'
                }.get(entry['file_type'], '[????]')
                
                print(f"  {type_name} {entry['name']:<30} (inode {entry['inode']})")
    
    def export_file_list(self, output_file):
        
        print(f"\n Xuat danh sach file -> {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("# EXT4 Directory Recovery - File List\n\n")
            
            if self.directory_tree:
                sorted_dirs = sorted(self.directory_tree.items(), key=lambda x: x[1]['path'])
                
                for inode_num, dir_info in sorted_dirs:
                    path = dir_info['path']
                    f.write(f"\n{path}:\n")
                    
                    for entry in dir_info['entries']:
                        if entry['name'] in ['.', '..']:
                            continue
                        
                        type_char = {1: 'F', 2: 'D', 7: 'L'}.get(entry['file_type'], '?')
                        f.write(f"  [{type_char}] {entry['name']} (inode {entry['inode']})\n")
            
            if self.found_inodes:
                f.write(f"\n\n# Total: {len(self.found_inodes)} inodes found\n")
        
        print(" Xuat thanh cong!")
