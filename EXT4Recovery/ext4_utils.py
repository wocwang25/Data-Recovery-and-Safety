

import struct
import os
from typing import Optional, Tuple
import hashlib
import binascii
from ext4_structures import *


class EXT4Utils:
    
    
    @staticmethod
    def read_block(file_path: str, block_number: int, block_size: int) -> Optional[bytes]:
        
        try:
            with open(file_path, 'rb') as f:
                offset = block_number * block_size
                f.seek(offset)
                data = f.read(block_size)
                if len(data) < block_size:
                    # Pad với zeros nếu đọc không đủ
                    data += b'\x00' * (block_size - len(data))
                return data
        except Exception as e:
            print(f"Lỗi khi đọc block {block_number}: {e}")
            return None
    
    @staticmethod
    def write_block(file_path: str, block_number: int, data: bytes, block_size: int) -> bool:
        
        try:
            with open(file_path, 'r+b') as f:
                offset = block_number * block_size
                f.seek(offset)
                # Đảm bảo data có đúng kích thước
                if len(data) < block_size:
                    data += b'\x00' * (block_size - len(data))
                elif len(data) > block_size:
                    data = data[:block_size]
                f.write(data)
                return True
        except Exception as e:
            print(f"Lỗi khi ghi block {block_number}: {e}")
            return False
    
    @staticmethod
    def read_bytes(file_path: str, offset: int, size: int) -> Optional[bytes]:
        
        try:
            with open(file_path, 'rb') as f:
                f.seek(offset)
                return f.read(size)
        except Exception as e:
            print(f"Lỗi khi đọc tại offset {offset}: {e}")
            return None
    
    @staticmethod
    def write_bytes(file_path: str, offset: int, data: bytes) -> bool:
        
        try:
            with open(file_path, 'r+b') as f:
                f.seek(offset)
                f.write(data)
                return True
        except Exception as e:
            print(f"Lỗi khi ghi tại offset {offset}: {e}")
            return False
    
    @staticmethod
    def bytes_to_int_le(data: bytes) -> int:
        
        return int.from_bytes(data, byteorder='little', signed=False)
    
    @staticmethod
    def int_to_bytes_le(value: int, size: int) -> bytes:
        
        return value.to_bytes(size, byteorder='little', signed=False)
    
    @staticmethod
    def is_buffer_empty(data: bytes) -> bool:
        
        return all(b == 0 for b in data)
    
    @staticmethod
    def calculate_crc32c(data: bytes) -> int:
        
        return binascii.crc32(data) & 0xffffffff
    
    @staticmethod
    def calculate_md5(data: str) -> str:
        
        return hashlib.md5(data.encode()).hexdigest()
    
    @staticmethod
    def parse_superblock(data: bytes) -> Optional[Superblock]:
        
        if len(data) < 1024:
            return None
        
        sb = Superblock()
        
        try:
            # Parse các trường cơ bản
            sb.s_inodes_count = struct.unpack('<I', data[0:4])[0]
            sb.s_blocks_count_lo = struct.unpack('<I', data[4:8])[0]
            sb.s_r_blocks_count_lo = struct.unpack('<I', data[8:12])[0]
            sb.s_free_blocks_count_lo = struct.unpack('<I', data[12:16])[0]
            sb.s_free_inodes_count = struct.unpack('<I', data[16:20])[0]
            sb.s_first_data_block = struct.unpack('<I', data[20:24])[0]
            sb.s_log_block_size = struct.unpack('<I', data[24:28])[0]
            sb.s_log_cluster_size = struct.unpack('<I', data[28:32])[0]
            sb.s_blocks_per_group = struct.unpack('<I', data[32:36])[0]
            sb.s_clusters_per_group = struct.unpack('<I', data[36:40])[0]
            sb.s_inodes_per_group = struct.unpack('<I', data[40:44])[0]
            sb.s_mtime = struct.unpack('<I', data[44:48])[0]
            sb.s_wtime = struct.unpack('<I', data[48:52])[0]
            sb.s_mnt_count = struct.unpack('<H', data[52:54])[0]
            sb.s_max_mnt_count = struct.unpack('<H', data[54:56])[0]
            sb.s_magic = struct.unpack('<H', data[56:58])[0]
            sb.s_state = struct.unpack('<H', data[58:60])[0]
            sb.s_errors = struct.unpack('<H', data[60:62])[0]
            sb.s_minor_rev_level = struct.unpack('<H', data[62:64])[0]
            sb.s_lastcheck = struct.unpack('<I', data[64:68])[0]
            sb.s_checkinterval = struct.unpack('<I', data[68:72])[0]
            sb.s_creator_os = struct.unpack('<I', data[72:76])[0]
            sb.s_rev_level = struct.unpack('<I', data[76:80])[0]
            sb.s_def_resuid = struct.unpack('<H', data[80:82])[0]
            sb.s_def_resgid = struct.unpack('<H', data[82:84])[0]
            
            # Dynamic revision fields
            sb.s_first_ino = struct.unpack('<I', data[84:88])[0]
            sb.s_inode_size = struct.unpack('<H', data[88:90])[0]
            sb.s_block_group_nr = struct.unpack('<H', data[90:92])[0]
            sb.s_feature_compat = struct.unpack('<I', data[92:96])[0]
            sb.s_feature_incompat = struct.unpack('<I', data[96:100])[0]
            sb.s_feature_ro_compat = struct.unpack('<I', data[100:104])[0]
            sb.s_uuid = data[104:120]
            sb.s_volume_name = data[120:136]
            sb.s_last_mounted = data[136:200]
            sb.s_algorithm_usage_bitmap = struct.unpack('<I', data[200:204])[0]
            
            # More fields...
            sb.s_prealloc_blocks = struct.unpack('<B', data[204:205])[0]
            sb.s_prealloc_dir_blocks = struct.unpack('<B', data[205:206])[0]
            sb.s_reserved_gdt_blocks = struct.unpack('<H', data[206:208])[0]
            
            # Journal
            sb.s_journal_uuid = data[208:224]
            sb.s_journal_inum = struct.unpack('<I', data[224:228])[0]
            sb.s_journal_dev = struct.unpack('<I', data[228:232])[0]
            sb.s_last_orphan = struct.unpack('<I', data[232:236])[0]
            
            # Hash seed
            hash_seed = struct.unpack('<IIII', data[236:252])
            sb.s_hash_seed = hash_seed
            sb.s_def_hash_version = struct.unpack('<B', data[252:253])[0]
            sb.s_jnl_backup_type = struct.unpack('<B', data[253:254])[0]
            sb.s_desc_size = struct.unpack('<H', data[254:256])[0]
            
            sb.s_default_mount_opts = struct.unpack('<I', data[256:260])[0]
            sb.s_first_meta_bg = struct.unpack('<I', data[260:264])[0]
            sb.s_mkfs_time = struct.unpack('<I', data[264:268])[0]
            
            # 64-bit support
            if len(data) >= 336:
                sb.s_blocks_count_hi = struct.unpack('<I', data[336:340])[0]
                sb.s_r_blocks_count_hi = struct.unpack('<I', data[340:344])[0]
                sb.s_free_blocks_count_hi = struct.unpack('<I', data[344:348])[0]
                sb.s_min_extra_isize = struct.unpack('<H', data[348:350])[0]
                sb.s_want_extra_isize = struct.unpack('<H', data[350:352])[0]
                sb.s_flags = struct.unpack('<I', data[352:356])[0]
            
            # Checksum (ở cuối)
            if len(data) >= 1024:
                sb.s_checksum = struct.unpack('<I', data[1020:1024])[0]
            
            return sb if sb.is_valid() else None
            
        except Exception as e:
            print(f"Lỗi khi parse superblock: {e}")
            return None
    
    @staticmethod
    def parse_group_descriptor(data: bytes, use_64bit: bool = False) -> Optional[GroupDescriptor]:
        
        if len(data) < 32:
            return None
        
        gd = GroupDescriptor()
        
        try:
            gd.bg_block_bitmap_lo = struct.unpack('<I', data[0:4])[0]
            gd.bg_inode_bitmap_lo = struct.unpack('<I', data[4:8])[0]
            gd.bg_inode_table_lo = struct.unpack('<I', data[8:12])[0]
            gd.bg_free_blocks_count_lo = struct.unpack('<H', data[12:14])[0]
            gd.bg_free_inodes_count_lo = struct.unpack('<H', data[14:16])[0]
            gd.bg_used_dirs_count_lo = struct.unpack('<H', data[16:18])[0]
            gd.bg_flags = struct.unpack('<H', data[18:20])[0]
            gd.bg_exclude_bitmap_lo = struct.unpack('<I', data[20:24])[0]
            gd.bg_block_bitmap_csum_lo = struct.unpack('<H', data[24:26])[0]
            gd.bg_inode_bitmap_csum_lo = struct.unpack('<H', data[26:28])[0]
            gd.bg_itable_unused_lo = struct.unpack('<H', data[28:30])[0]
            gd.bg_checksum = struct.unpack('<H', data[30:32])[0]
            
            # 64-bit fields
            if use_64bit and len(data) >= 64:
                gd.bg_block_bitmap_hi = struct.unpack('<I', data[32:36])[0]
                gd.bg_inode_bitmap_hi = struct.unpack('<I', data[36:40])[0]
                gd.bg_inode_table_hi = struct.unpack('<I', data[40:44])[0]
                gd.bg_free_blocks_count_hi = struct.unpack('<H', data[44:46])[0]
                gd.bg_free_inodes_count_hi = struct.unpack('<H', data[46:48])[0]
                gd.bg_used_dirs_count_hi = struct.unpack('<H', data[48:50])[0]
                gd.bg_itable_unused_hi = struct.unpack('<H', data[50:52])[0]
                gd.bg_exclude_bitmap_hi = struct.unpack('<I', data[52:56])[0]
                gd.bg_block_bitmap_csum_hi = struct.unpack('<H', data[56:58])[0]
                gd.bg_inode_bitmap_csum_hi = struct.unpack('<H', data[58:60])[0]
            
            return gd
            
        except Exception as e:
            print(f"Lỗi khi parse group descriptor: {e}")
            return None
    
    @staticmethod
    def parse_inode(data: bytes) -> Optional[Inode]:
        
        if len(data) < 128:
            return None
        
        inode = Inode()
        
        try:
            inode.i_mode = struct.unpack('<H', data[0:2])[0]
            inode.i_uid = struct.unpack('<H', data[2:4])[0]
            inode.i_size_lo = struct.unpack('<I', data[4:8])[0]
            inode.i_atime = struct.unpack('<I', data[8:12])[0]
            inode.i_ctime = struct.unpack('<I', data[12:16])[0]
            inode.i_mtime = struct.unpack('<I', data[16:20])[0]
            inode.i_dtime = struct.unpack('<I', data[20:24])[0]
            inode.i_gid = struct.unpack('<H', data[24:26])[0]
            inode.i_links_count = struct.unpack('<H', data[26:28])[0]
            inode.i_blocks_lo = struct.unpack('<I', data[28:32])[0]
            inode.i_flags = struct.unpack('<I', data[32:36])[0]
            inode.i_osd1 = struct.unpack('<I', data[36:40])[0]
            
            # i_block[15] - 60 bytes
            i_block = struct.unpack('<15I', data[40:100])
            inode.i_block = i_block
            
            inode.i_generation = struct.unpack('<I', data[100:104])[0]
            inode.i_file_acl_lo = struct.unpack('<I', data[104:108])[0]
            inode.i_size_high = struct.unpack('<I', data[108:112])[0]
            inode.i_obso_faddr = struct.unpack('<I', data[112:116])[0]
            inode.i_osd2 = data[116:128]
            
            # Extra inode fields (nếu inode > 128 bytes)
            if len(data) >= 256:
                inode.i_extra_isize = struct.unpack('<H', data[128:130])[0]
                inode.i_checksum_hi = struct.unpack('<H', data[130:132])[0]
                inode.i_ctime_extra = struct.unpack('<I', data[132:136])[0]
                inode.i_mtime_extra = struct.unpack('<I', data[136:140])[0]
                inode.i_atime_extra = struct.unpack('<I', data[140:144])[0]
                inode.i_crtime = struct.unpack('<I', data[144:148])[0]
                inode.i_crtime_extra = struct.unpack('<I', data[148:152])[0]
                inode.i_version_hi = struct.unpack('<I', data[152:156])[0]
            
            return inode
            
        except Exception as e:
            print(f"Lỗi khi parse inode: {e}")
            return None
    
    @staticmethod
    def format_bytes(size: int) -> str:
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    @staticmethod
    def print_hex_dump(data: bytes, offset: int = 0, length: int = None):
        
        if length is None:
            length = len(data)
        
        for i in range(0, length, 16):
            # Offset
            print(f"{offset + i:08x}  ", end="")
            
            # Hex values
            hex_str = ""
            ascii_str = ""
            for j in range(16):
                if i + j < length:
                    byte = data[i + j]
                    hex_str += f"{byte:02x} "
                    ascii_str += chr(byte) if 32 <= byte < 127 else "."
                else:
                    hex_str += "   "
                
                if j == 7:
                    hex_str += " "
            
            print(f"{hex_str} |{ascii_str}|")
