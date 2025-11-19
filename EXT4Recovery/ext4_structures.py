"""
EXT4 File System Structures
Định nghĩa các cấu trúc dữ liệu cơ bản của EXT4 filesystem
Tham khảo: https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout
"""

import struct
from typing import Optional
from dataclasses import dataclass
import hashlib


@dataclass
class Superblock:
    """
    EXT4 Superblock - 1024 bytes
    Chứa thông tin cấu hình và metadata của filesystem
    """
    # Offset 0x00
    s_inodes_count: int = 0          # Tổng số inodes
    s_blocks_count_lo: int = 0       # Tổng số blocks (32 bit thấp)
    s_r_blocks_count_lo: int = 0     # Số blocks dành riêng
    s_free_blocks_count_lo: int = 0  # Số blocks trống
    s_free_inodes_count: int = 0     # Số inodes trống
    s_first_data_block: int = 0      # Block đầu tiên chứa dữ liệu
    s_log_block_size: int = 0        # Block size = 1024 << s_log_block_size
    s_log_cluster_size: int = 0      # Cluster size
    s_blocks_per_group: int = 0      # Số blocks mỗi block group
    s_clusters_per_group: int = 0    # Số clusters mỗi block group
    s_inodes_per_group: int = 0      # Số inodes mỗi block group
    s_mtime: int = 0                 # Mount time
    s_wtime: int = 0                 # Write time
    s_mnt_count: int = 0             # Mount count
    s_max_mnt_count: int = 0         # Maximum mount count
    s_magic: int = 0xEF53            # Magic signature (0xEF53)
    s_state: int = 0                 # File system state
    s_errors: int = 0                # Behaviour when detecting errors
    s_minor_rev_level: int = 0       # Minor revision level
    s_lastcheck: int = 0             # Time of last check
    s_checkinterval: int = 0         # Max time between checks
    s_creator_os: int = 0            # OS
    s_rev_level: int = 0             # Revision level
    s_def_resuid: int = 0            # Default uid for reserved blocks
    s_def_resgid: int = 0            # Default gid for reserved blocks
    
    # EXT4 dynamic revision
    s_first_ino: int = 11            # First non-reserved inode
    s_inode_size: int = 256          # Size of inode structure
    s_block_group_nr: int = 0        # Block group số của superblock này
    s_feature_compat: int = 0        # Compatible feature set
    s_feature_incompat: int = 0      # Incompatible feature set
    s_feature_ro_compat: int = 0     # Readonly-compatible feature set
    s_uuid: bytes = b'\x00' * 16     # 128-bit UUID
    s_volume_name: bytes = b'\x00' * 16  # Volume name
    s_last_mounted: bytes = b'\x00' * 64  # Directory where last mounted
    s_algorithm_usage_bitmap: int = 0 # For compression
    
    s_prealloc_blocks: int = 0       # Số blocks để preallocate cho files
    s_prealloc_dir_blocks: int = 0   # Số blocks để preallocate cho directories
    s_reserved_gdt_blocks: int = 0   # Số blocks reserved cho GDT mở rộng
    
    # Journaling support
    s_journal_uuid: bytes = b'\x00' * 16  # UUID của journal superblock
    s_journal_inum: int = 0          # Inode number của journal file
    s_journal_dev: int = 0           # Device number của journal file
    s_last_orphan: int = 0           # Head của list orphan inodes
    
    # Directory indexing support
    s_hash_seed: tuple = (0, 0, 0, 0)  # HTREE hash seed
    s_def_hash_version: int = 0      # Default hash version
    s_jnl_backup_type: int = 0
    s_desc_size: int = 32            # Size của group descriptor
    s_default_mount_opts: int = 0
    s_first_meta_bg: int = 0         # First metablock block group
    s_mkfs_time: int = 0             # Khi filesystem được tạo
    s_jnl_blocks: tuple = tuple([0] * 17)  # Backup của journal inode
    
    # 64bit support
    s_blocks_count_hi: int = 0       # Blocks count (32 bit cao)
    s_r_blocks_count_hi: int = 0     # Reserved blocks count (32 bit cao)
    s_free_blocks_count_hi: int = 0  # Free blocks count (32 bit cao)
    s_min_extra_isize: int = 0       # Minimum extra inode size
    s_want_extra_isize: int = 0      # Desired extra inode size
    s_flags: int = 0                 # Miscellaneous flags
    s_raid_stride: int = 0           # RAID stride
    s_mmp_interval: int = 0          # Số giây trong MMP checking
    s_mmp_block: int = 0             # Block cho multi-mount protection
    s_raid_stripe_width: int = 0     # blocks on all data disks (N*stride)
    s_log_groups_per_flex: int = 0   # FLEX_BG group size
    s_checksum_type: int = 0         # Metadata checksum algorithm type
    s_reserved_pad: int = 0
    s_kbytes_written: int = 0        # Số KiB written đến filesystem
    s_snapshot_inum: int = 0         # Inode number của active snapshot
    s_snapshot_id: int = 0           # Sequential ID của active snapshot
    s_snapshot_r_blocks_count: int = 0  # Số blocks reserved cho active snapshot
    s_snapshot_list: int = 0         # Inode number của head của snapshot list
    s_error_count: int = 0           # Số lỗi file system errors
    s_first_error_time: int = 0      # First time an error happened
    s_first_error_ino: int = 0       # Inode involved in first error
    s_first_error_block: int = 0     # Block involved in first error
    s_first_error_func: bytes = b'\x00' * 32  # Function where error happened
    s_first_error_line: int = 0      # Line number where error happened
    s_last_error_time: int = 0       # Most recent time of an error
    s_last_error_ino: int = 0        # Inode involved in last error
    s_last_error_line: int = 0       # Line number where error happened
    s_last_error_block: int = 0      # Block involved in last error
    s_last_error_func: bytes = b'\x00' * 32  # Function where error happened
    s_mount_opts: bytes = b'\x00' * 64  # Mount options
    s_usr_quota_inum: int = 0        # Inode của user quota file
    s_grp_quota_inum: int = 0        # Inode của group quota file
    s_overhead_blocks: int = 0       # Overhead blocks/clusters
    s_backup_bgs: tuple = (0, 0)     # Block groups chứa superblock backups
    s_encrypt_algos: bytes = b'\x00' * 4  # Encryption algorithms
    s_encrypt_pw_salt: bytes = b'\x00' * 16  # Salt for string2key algorithm
    s_lpf_ino: int = 0               # Location của lost+found inode
    s_prj_quota_inum: int = 0        # Inode cho tracking project quotas
    s_checksum_seed: int = 0         # Checksum seed
    s_reserved: tuple = tuple([0] * 98)  # Padding đến end of block
    s_checksum: int = 0              # Superblock checksum
    
    def get_block_size(self) -> int:
        """Tính block size từ s_log_block_size"""
        return 1024 << self.s_log_block_size
    
    def get_total_blocks(self) -> int:
        """Tính tổng số blocks (64-bit)"""
        return (self.s_blocks_count_hi << 32) | self.s_blocks_count_lo
    
    def is_valid(self) -> bool:
        """Kiểm tra superblock có hợp lệ không"""
        return self.s_magic == 0xEF53
    
    def calculate_checksum(self, data: bytes) -> int:
        """Tính checksum của superblock"""
        # CRC32c checksum
        import binascii
        return binascii.crc32(data) & 0xffffffff


@dataclass
class GroupDescriptor:
    """
    EXT4 Block Group Descriptor - 32 bytes (hoặc 64 bytes với 64bit feature)
    Chứa thông tin về một block group
    """
    bg_block_bitmap_lo: int = 0      # Block bitmap block (32 bit thấp)
    bg_inode_bitmap_lo: int = 0      # Inode bitmap block (32 bit thấp)
    bg_inode_table_lo: int = 0       # Inode table block (32 bit thấp)
    bg_free_blocks_count_lo: int = 0 # Số free blocks (16 bit thấp)
    bg_free_inodes_count_lo: int = 0 # Số free inodes (16 bit thấp)
    bg_used_dirs_count_lo: int = 0   # Số directories (16 bit thấp)
    bg_flags: int = 0                # Flags (INODE_UNINIT, BLOCK_UNINIT, INODE_ZEROED)
    bg_exclude_bitmap_lo: int = 0    # Snapshot exclude bitmap
    bg_block_bitmap_csum_lo: int = 0 # Block bitmap checksum
    bg_inode_bitmap_csum_lo: int = 0 # Inode bitmap checksum
    bg_itable_unused_lo: int = 0     # Số unused inodes
    bg_checksum: int = 0             # Group descriptor checksum
    
    # Chỉ có khi INCOMPAT_64BIT được set
    bg_block_bitmap_hi: int = 0      # Block bitmap block (32 bit cao)
    bg_inode_bitmap_hi: int = 0      # Inode bitmap block (32 bit cao)
    bg_inode_table_hi: int = 0       # Inode table block (32 bit cao)
    bg_free_blocks_count_hi: int = 0 # Số free blocks (16 bit cao)
    bg_free_inodes_count_hi: int = 0 # Số free inodes (16 bit cao)
    bg_used_dirs_count_hi: int = 0   # Số directories (16 bit cao)
    bg_itable_unused_hi: int = 0     # Số unused inodes (16 bit cao)
    bg_exclude_bitmap_hi: int = 0    # Snapshot exclude bitmap
    bg_block_bitmap_csum_hi: int = 0 # Block bitmap checksum
    bg_inode_bitmap_csum_hi: int = 0 # Inode bitmap checksum
    bg_reserved: int = 0
    
    def get_block_bitmap(self) -> int:
        """Lấy địa chỉ block bitmap (64-bit)"""
        return (self.bg_block_bitmap_hi << 32) | self.bg_block_bitmap_lo
    
    def get_inode_bitmap(self) -> int:
        """Lấy địa chỉ inode bitmap (64-bit)"""
        return (self.bg_inode_bitmap_hi << 32) | self.bg_inode_bitmap_lo
    
    def get_inode_table(self) -> int:
        """Lấy địa chỉ inode table (64-bit)"""
        return (self.bg_inode_table_hi << 32) | self.bg_inode_table_lo


@dataclass
class Inode:
    """
    EXT4 Inode - 256 bytes (hoặc lớn hơn)
    Chứa metadata của file/directory
    """
    i_mode: int = 0                  # File mode (quyền và loại file)
    i_uid: int = 0                   # Owner UID (16 bit thấp)
    i_size_lo: int = 0               # File size (32 bit thấp)
    i_atime: int = 0                 # Access time
    i_ctime: int = 0                 # Change time
    i_mtime: int = 0                 # Modification time
    i_dtime: int = 0                 # Deletion time
    i_gid: int = 0                   # Group ID (16 bit thấp)
    i_links_count: int = 0           # Hard links count
    i_blocks_lo: int = 0             # Số 512-byte blocks (32 bit thấp)
    i_flags: int = 0                 # File flags
    i_osd1: int = 0                  # OS dependent
    i_block: tuple = tuple([0] * 15) # Pointers đến data blocks (60 bytes)
    i_generation: int = 0            # File version (for NFS)
    i_file_acl_lo: int = 0           # Extended attributes (32 bit thấp)
    i_size_high: int = 0             # File size (32 bit cao) / i_dir_acl
    i_obso_faddr: int = 0            # Obsoleted fragment address
    i_osd2: bytes = b'\x00' * 12     # OS dependent
    i_extra_isize: int = 0           # Size của extra inode space
    i_checksum_hi: int = 0           # Inode checksum (16 bit cao)
    i_ctime_extra: int = 0           # Extra change time bits
    i_mtime_extra: int = 0           # Extra modification time bits
    i_atime_extra: int = 0           # Extra access time bits
    i_crtime: int = 0                # File creation time
    i_crtime_extra: int = 0          # Extra file creation time bits
    i_version_hi: int = 0            # Version (32 bit cao)
    i_projid: int = 0                # Project ID
    
    def get_size(self) -> int:
        """Lấy kích thước file (64-bit)"""
        return (self.i_size_high << 32) | self.i_size_lo
    
    def is_directory(self) -> bool:
        """Kiểm tra có phải directory không"""
        return (self.i_mode & 0xF000) == 0x4000
    
    def is_regular_file(self) -> bool:
        """Kiểm tra có phải file thông thường không"""
        return (self.i_mode & 0xF000) == 0x8000
    
    def is_symlink(self) -> bool:
        """Kiểm tra có phải symbolic link không"""
        return (self.i_mode & 0xF000) == 0xA000


@dataclass
class DirectoryEntry:
    """
    EXT4 Directory Entry
    Chứa thông tin về một entry trong directory
    """
    inode: int = 0                   # Inode number
    rec_len: int = 0                 # Length của directory entry
    name_len: int = 0                # Length của tên file
    file_type: int = 0               # File type
    name: str = ""                   # Tên file/directory
    
    # File types
    FT_UNKNOWN = 0
    FT_REG_FILE = 1
    FT_DIR = 2
    FT_CHRDEV = 3
    FT_BLKDEV = 4
    FT_FIFO = 5
    FT_SOCK = 6
    FT_SYMLINK = 7
    
    def get_type_name(self) -> str:
        """Lấy tên loại file"""
        types = {
            0: "Unknown",
            1: "Regular File",
            2: "Directory",
            3: "Character Device",
            4: "Block Device",
            5: "FIFO",
            6: "Socket",
            7: "Symbolic Link"
        }
        return types.get(self.file_type, "Unknown")


@dataclass
class ExtentHeader:
    """
    EXT4 Extent Header
    Header cho extent tree
    """
    eh_magic: int = 0xF30A           # Magic number
    eh_entries: int = 0              # Số entries trong node này
    eh_max: int = 0                  # Maximum số entries
    eh_depth: int = 0                # Độ sâu của tree (0 = leaf)
    eh_generation: int = 0           # Generation của tree
    
    def is_valid(self) -> bool:
        """Kiểm tra header có hợp lệ không"""
        return self.eh_magic == 0xF30A


@dataclass
class Extent:
    """
    EXT4 Extent - 12 bytes
    Mô tả một phạm vi blocks liên tục
    """
    ee_block: int = 0                # First logical block
    ee_len: int = 0                  # Số blocks
    ee_start_hi: int = 0             # Physical block (16 bit cao)
    ee_start_lo: int = 0             # Physical block (32 bit thấp)
    
    def get_start_block(self) -> int:
        """Lấy physical block đầu tiên (48-bit)"""
        return (self.ee_start_hi << 32) | self.ee_start_lo
    
    def is_uninitialized(self) -> bool:
        """Kiểm tra extent có được khởi tạo chưa"""
        return self.ee_len > 32768  # Bit cao được set
    
    def get_length(self) -> int:
        """Lấy độ dài thực của extent"""
        if self.is_uninitialized():
            return self.ee_len - 32768
        return self.ee_len


# Constants
EXT4_SUPER_MAGIC = 0xEF53
EXT4_SUPERBLOCK_OFFSET = 1024
EXT4_SUPERBLOCK_SIZE = 1024
EXT4_MIN_BLOCK_SIZE = 1024
EXT4_MAX_BLOCK_SIZE = 65536

# Feature flags
EXT4_FEATURE_INCOMPAT_EXTENTS = 0x0040
EXT4_FEATURE_INCOMPAT_64BIT = 0x0080
EXT4_FEATURE_INCOMPAT_FLEX_BG = 0x0200

# Inode flags
EXT4_EXTENTS_FL = 0x00080000  # Inode sử dụng extents
