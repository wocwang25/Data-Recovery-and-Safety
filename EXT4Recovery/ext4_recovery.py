import os
from typing import List, Optional, Tuple, Dict
from datetime import datetime
from ext4_structures import *
from ext4_utils import EXT4Utils

class EXT4Recovery:
    def __init__(self, device_path: str = None):
        
        self.device_path = device_path
        self.superblock: Optional[Superblock] = None
        self.backup_superblocks: List[Tuple[int, Superblock]] = []
        self.group_descriptors: List[GroupDescriptor] = []
        self.block_size = 0
        self.total_groups = 0
        self.utils = EXT4Utils()
        self.is_64bit = False

    def open_device(self, device_path: str) -> bool:
        
        if not os.path.exists(device_path):
            print(f" Không tìm thấy device/file: {device_path}")
            return False

        self.device_path = device_path

        # Thử đọc superblock chính
        print(f"\n Đang mở: {device_path}")
        print("=" * 60)

        if self.read_primary_superblock():
            print(" Đọc superblock chính thành công!")
            return True
        else:
            print("  Superblock chính bị hỏng, đang tìm backup...")
            return self.find_backup_superblocks()

    def read_primary_superblock(self) -> bool:
        
        data = self.utils.read_bytes(self.device_path,
                                     EXT4_SUPERBLOCK_OFFSET,
                                     EXT4_SUPERBLOCK_SIZE)
        if not data:
            return False

        self.superblock = self.utils.parse_superblock(data)
        if not self.superblock or not self.superblock.is_valid():
            return False

        # Cập nhật các thông tin cơ bản
        self.block_size = self.superblock.get_block_size()
        self.is_64bit = (self.superblock.s_feature_incompat &
                        EXT4_FEATURE_INCOMPAT_64BIT) != 0

        # Tính số block groups
        total_blocks = self.superblock.get_total_blocks()
        self.total_groups = (total_blocks + self.superblock.s_blocks_per_group - 1) // \
                           self.superblock.s_blocks_per_group

        return True

    def find_backup_superblocks(self) -> bool:
        
        print("\n Đang quét tìm backup superblocks...")

        # Thử với các kích thước block phổ biến
        possible_block_sizes = [1024, 2048, 4096]

        for block_size in possible_block_sizes:
            print(f"\n  Thử với block size = {block_size} bytes")

            # Tính blocks_per_group theo block_size (giá trị mặc định EXT4)
            blocks_per_group = 8 * block_size  # 8192 cho 1KB, 16384 cho 2KB, 32768 cho 4KB

            # Backup superblocks thường ở các block groups: 1, 3, 5, 7, 9, 27, 49, 81, ...
            backup_groups = [1]

            # Thêm các lũy thừa của 3, 5, 7
            for base in [3, 5, 7]:
                power = base
                while power < 100:  # Giới hạn tìm kiếm
                    backup_groups.append(power)
                    power *= base

            backup_groups = sorted(set(backup_groups))  # Loại trùng và sắp xếp

            for group_num in backup_groups[:15]:  # Kiểm tra 15 groups đầu tiên
                # Tính offset của superblock trong group này
                # Block đầu tiên của group
                group_start_block = group_num * blocks_per_group
                
                # Offset tính bằng bytes
                if block_size == 1024:
                    # Với block size 1024, superblock ở block thứ 1 của group (block 0 là boot block)
                    # Superblock bắt đầu ở byte offset 1024 trong group
                    offset = group_start_block * block_size + 1024
                else:
                    # Với block size >= 2048, superblock ở đầu block đầu tiên của group
                    # Không cần thêm 1024 bytes offset
                    offset = group_start_block * block_size

                # Đảm bảo không vượt quá kích thước file
                try:
                    file_size = os.path.getsize(self.device_path)
                    if offset + 1024 > file_size:
                        continue
                except:
                    pass

                data = self.utils.read_bytes(self.device_path, offset, 1024)
                if data:
                    sb = self.utils.parse_superblock(data)
                    if sb and sb.is_valid():
                        self.backup_superblocks.append((group_num, sb))
                        print(f"   Tìm thấy backup tại group {group_num} (offset: {offset})")

            if self.backup_superblocks:
                # Sử dụng backup đầu tiên làm superblock chính
                self.superblock = self.backup_superblocks[0][1]
                self.block_size = self.superblock.get_block_size()
                self.is_64bit = (self.superblock.s_feature_incompat &
                                EXT4_FEATURE_INCOMPAT_64BIT) != 0

                total_blocks = self.superblock.get_total_blocks()
                self.total_groups = (total_blocks + self.superblock.s_blocks_per_group - 1) // \
                                   self.superblock.s_blocks_per_group

                print(f"\n Tìm thấy {len(self.backup_superblocks)} backup superblock(s)")
                return True

        print(" Không tìm thấy backup superblock nào hợp lệ")
        return False

    def read_group_descriptors(self) -> bool:
        
        if not self.superblock:
            return False

        print(f"\n Đang đọc {self.total_groups} group descriptors...")

        # Group descriptor table bắt đầu sau superblock
        if self.block_size == 1024:
            gdt_block = 2  # Block 2 nếu block size = 1024
        else:
            gdt_block = 1  # Block 1 nếu block size > 1024

        desc_size = self.superblock.s_desc_size if self.is_64bit else 32

        # Đọc toàn bộ GDT
        gdt_blocks = (self.total_groups * desc_size + self.block_size - 1) // self.block_size

        for i in range(gdt_blocks):
            data = self.utils.read_block(self.device_path, gdt_block + i, self.block_size)
            if not data:
                continue

            # Parse từng group descriptor
            for j in range(0, self.block_size, desc_size):
                if len(self.group_descriptors) >= self.total_groups:
                    break

                gd_data = data[j:j + desc_size]
                gd = self.utils.parse_group_descriptor(gd_data, self.is_64bit)
                if gd:
                    self.group_descriptors.append(gd)

        print(f" Đọc thành công {len(self.group_descriptors)} group descriptors")
        return len(self.group_descriptors) > 0

    def print_superblock_info(self):
        
        if not self.superblock:
            print(" Chưa có superblock")
            return

        sb = self.superblock

        print("\n" + "=" * 60)
        print(" THÔNG TIN SUPERBLOCK")
        print("=" * 60)

        print(f"Magic Number:          0x{sb.s_magic:04X} {' (Hợp lệ)' if sb.is_valid() else ' (Không hợp lệ)'}")
        print(f"Revision Level:        {sb.s_rev_level}")
        print(f"Block Size:            {self.block_size} bytes")
        print(f"Total Blocks:          {sb.get_total_blocks():,}")
        print(f"Free Blocks:           {sb.s_free_blocks_count_lo:,}")
        print(f"Total Inodes:          {sb.s_inodes_count:,}")
        print(f"Free Inodes:           {sb.s_free_inodes_count:,}")
        print(f"Blocks Per Group:      {sb.s_blocks_per_group:,}")
        print(f"Inodes Per Group:      {sb.s_inodes_per_group:,}")
        print(f"Total Block Groups:    {self.total_groups}")
        print(f"Inode Size:            {sb.s_inode_size} bytes")
        print(f"First Inode:           {sb.s_first_ino}")

        # Volume name
        vol_name = sb.s_volume_name.decode('utf-8', errors='ignore').rstrip('\x00')
        if vol_name:
            print(f"Volume Name:           {vol_name}")

        # UUID
        uuid_str = '-'.join([
            sb.s_uuid[0:4].hex(),
            sb.s_uuid[4:6].hex(),
            sb.s_uuid[6:8].hex(),
            sb.s_uuid[8:10].hex(),
            sb.s_uuid[10:16].hex()
        ])
        print(f"UUID:                  {uuid_str}")

        # Last mounted
        last_mounted = sb.s_last_mounted.decode('utf-8', errors='ignore').rstrip('\x00')
        if last_mounted:
            print(f"Last Mounted:          {last_mounted}")

        # Times
        if sb.s_mtime > 0:
            print(f"Last Mount Time:       {datetime.fromtimestamp(sb.s_mtime)}")
        if sb.s_wtime > 0:
            print(f"Last Write Time:       {datetime.fromtimestamp(sb.s_wtime)}")
        if sb.s_mkfs_time > 0:
            print(f"Created Time:          {datetime.fromtimestamp(sb.s_mkfs_time)}")

        # Features
        print(f"\n Features:")
        print(f"  Compatible:          0x{sb.s_feature_compat:08X}")
        print(f"  Incompatible:        0x{sb.s_feature_incompat:08X}")
        print(f"  Read-only Compatible: 0x{sb.s_feature_ro_compat:08X}")

        if sb.s_feature_incompat & EXT4_FEATURE_INCOMPAT_EXTENTS:
            print(f"   Extents")
        if sb.s_feature_incompat & EXT4_FEATURE_INCOMPAT_64BIT:
            print(f"   64-bit")
        if sb.s_feature_incompat & EXT4_FEATURE_INCOMPAT_FLEX_BG:
            print(f"   Flexible Block Groups")

        # Capacity
        total_size = sb.get_total_blocks() * self.block_size
        free_size = sb.s_free_blocks_count_lo * self.block_size
        used_size = total_size - free_size

        print(f"\n Dung lượng:")
        print(f"  Total:               {self.utils.format_bytes(total_size)}")
        print(f"  Used:                {self.utils.format_bytes(used_size)}")
        print(f"  Free:                {self.utils.format_bytes(free_size)}")
        print(f"  Usage:               {(used_size / total_size * 100):.1f}%")

        print("=" * 60)

    def read_inode(self, inode_number: int) -> Optional[Inode]:
        
        if not self.superblock or not self.group_descriptors:
            return None

        # Tính group và index trong group
        group_num = (inode_number - 1) // self.superblock.s_inodes_per_group
        local_index = (inode_number - 1) % self.superblock.s_inodes_per_group

        if group_num >= len(self.group_descriptors):
            return None

        # Lấy địa chỉ inode table
        gd = self.group_descriptors[group_num]
        inode_table_block = gd.get_inode_table()

        # Tính offset của inode
        inode_offset = inode_table_block * self.block_size + \
                      local_index * self.superblock.s_inode_size

        # Đọc dữ liệu inode
        data = self.utils.read_bytes(self.device_path,
                                     inode_offset,
                                     self.superblock.s_inode_size)
        if not data:
            return None

        return self.utils.parse_inode(data)

    def list_directory(self, inode_number: int = 2) -> List[DirectoryEntry]:
        
        inode = self.read_inode(inode_number)
        if not inode or not inode.is_directory():
            print(f" Inode {inode_number} không phải directory")
            return []

        entries = []

        # Kiểm tra xem có sử dụng extents không
        if inode.i_flags & EXT4_EXTENTS_FL:
            # Sử dụng extent tree
            entries = self._list_directory_extents(inode)
        else:
            # Sử dụng block pointers truyền thống
            entries = self._list_directory_blocks(inode)

        return entries

    def _list_directory_blocks(self, inode: Inode) -> List[DirectoryEntry]:
        
        entries = []

        # Đọc các direct blocks
        for i in range(12):
            block_num = inode.i_block[i]
            if block_num == 0:
                break

            data = self.utils.read_block(self.device_path, block_num, self.block_size)
            if data:
                entries.extend(self._parse_directory_entries(data))

        return entries

    def _list_directory_extents(self, inode: Inode) -> List[DirectoryEntry]:
        
        # i_block chứa extent header và extents
        # Đây là implementation đơn giản, chỉ xử lý leaf extents
        entries = []

        # Parse extent header từ i_block
        # (Implementation chi tiết hơn sẽ cần xử lý extent tree đầy đủ)

        return entries

    def _parse_directory_entries(self, data: bytes) -> List[DirectoryEntry]:
        
        entries = []
        offset = 0

        while offset < len(data):
            if offset + 8 > len(data):
                break

            # Parse directory entry header
            inode_num = struct.unpack('<I', data[offset:offset+4])[0]
            rec_len = struct.unpack('<H', data[offset+4:offset+6])[0]
            name_len = struct.unpack('<B', data[offset+6:offset+7])[0]
            file_type = struct.unpack('<B', data[offset+7:offset+8])[0]

            if inode_num == 0 or rec_len == 0:
                break

            # Parse filename
            name = data[offset+8:offset+8+name_len].decode('utf-8', errors='ignore')

            entry = DirectoryEntry(
                inode=inode_num,
                rec_len=rec_len,
                name_len=name_len,
                file_type=file_type,
                name=name
            )
            entries.append(entry)

            offset += rec_len

        return entries

    def scan_for_inodes(self, start_block: int = 0, num_blocks: int = 100) -> List[int]:
        
        print(f"\n Đang quét tìm inodes từ block {start_block}...")
        found_inodes = []

        for block_num in range(start_block, start_block + num_blocks):
            data = self.utils.read_block(self.device_path, block_num, self.block_size)
            if not data:
                continue

            # Quét từng offset có thể là inode
            for offset in range(0, self.block_size, 256):
                inode_data = data[offset:offset+256]
                inode = self.utils.parse_inode(inode_data)

                if inode and inode.i_links_count > 0:
                    # Tính inode number từ vị trí
                    inode_num = (block_num * self.block_size + offset) // 256
                    found_inodes.append(inode_num)

        print(f" Tìm thấy {len(found_inodes)} inodes")
        return found_inodes

    def recover_file(self, inode_number: int, output_path: str) -> bool:
        
        print(f"\n Đang phục hồi inode {inode_number}...")

        inode = self.read_inode(inode_number)
        if not inode:
            print(" Không thể đọc inode")
            return False

        if not inode.is_regular_file():
            print(" Không phải file thông thường")
            return False

        file_size = inode.get_size()
        print(f"  Kích thước: {self.utils.format_bytes(file_size)}")

        try:
            with open(output_path, 'wb') as f:
                bytes_written = 0

                # Đọc data từ blocks
                if inode.i_flags & EXT4_EXTENTS_FL:
                    # Sử dụng extents (cần implementation đầy đủ)
                    print("  File sử dụng extents (chưa hỗ trợ đầy đủ)")
                    return False
                else:
                    # Sử dụng block pointers
                    for i in range(12):
                        if bytes_written >= file_size:
                            break

                        block_num = inode.i_block[i]
                        if block_num == 0:
                            break

                        data = self.utils.read_block(self.device_path,
                                                     block_num,
                                                     self.block_size)
                        if data:
                            # Chỉ ghi số bytes còn lại
                            to_write = min(len(data), file_size - bytes_written)
                            f.write(data[:to_write])
                            bytes_written += to_write

            print(f" Đã phục hồi {self.utils.format_bytes(bytes_written)} vào {output_path}")
            return True

        except Exception as e:
            print(f" Lỗi khi phục hồi file: {e}")
            return False

    def generate_recovery_report(self) -> str:
        
        report = []
        report.append("=" * 60)
        report.append("BÁO CÁO PHỤC HỒI DỮ LIỆU EXT4")
        report.append("=" * 60)
        report.append(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Device: {self.device_path}")
        report.append("")

        if self.superblock:
            report.append(" Trạng thái Superblock: Hợp lệ")
            report.append(f"   Block Size: {self.block_size} bytes")
            report.append(f"   Total Blocks: {self.superblock.get_total_blocks():,}")
            report.append(f"   Total Inodes: {self.superblock.s_inodes_count:,}")
        else:
            report.append(" Trạng thái Superblock: Không hợp lệ")

        if self.backup_superblocks:
            report.append(f"\n Backup Superblocks: Tìm thấy {len(self.backup_superblocks)}")
            for group_num, sb in self.backup_superblocks[:5]:
                report.append(f"   - Group {group_num}")

        if self.group_descriptors:
            report.append(f"\n Group Descriptors: {len(self.group_descriptors)}/{self.total_groups}")

        report.append("\n" + "=" * 60)

        return "\n".join(report)
