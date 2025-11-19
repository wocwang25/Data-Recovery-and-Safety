#!/usr/bin/env python3

import sys
import os
import struct

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_structures import *
from ext4_utils import EXT4Utils


class PartitionScanner:
    

    def __init__(self, device_path):
        self.device_path = device_path
        self.found_partitions = []
        self.utils = EXT4Utils()

    def scan_for_ext4(self, max_size_gb=100):
        
        print("\n" + "=" * 70)
        print("QUET DISK TIM EXT4 FILESYSTEMS")
        print("=" * 70)
        
        if not os.path.exists(self.device_path):
            print(f"Loi: File khong ton tai: {self.device_path}")
            return False
        
        file_size = os.path.getsize(self.device_path)
        print(f"\nFile: {self.device_path}")
        print(f"Size: {file_size:,} bytes ({file_size / 1024**3:.2f} GB)")
        
        max_scan = min(file_size, max_size_gb * 1024**3)
        print(f"Quet toi da: {max_scan / 1024**3:.2f} GB")
        
        print("\nDang quet...")
        
        # Quet theo block 1MB de tang toc
        scan_step = 1024 * 1024  # 1MB
        scanned = 0
        
        for offset in range(0, max_scan, scan_step):
            # Hien thi tien do
            if offset % (100 * 1024 * 1024) == 0:  # Moi 100MB
                percent = (offset / max_scan) * 100
                print(f"  Tien do: {percent:.1f}% ({offset / 1024**3:.2f} GB)", end='\r')
            
            # Doc 2 bytes tai vi tri magic number
            # EXT4 magic: offset + 1024 (superblock) + 56 (magic offset)
            magic_offset = offset + 1024 + 56
            
            if magic_offset + 2 > file_size:
                break
            
            data = self.utils.read_bytes(self.device_path, magic_offset, 2)
            
            if data and len(data) == 2:
                magic = struct.unpack('<H', data)[0]
                
                if magic == 0xEF53:
                    # Tim thay EXT4!
                    print(f"\n\n  Tim thay EXT4 tai offset: {offset:,} bytes")
                    
                    # Doc superblock day du
                    sb_offset = offset + 1024
                    sb_data = self.utils.read_bytes(self.device_path, sb_offset, 1024)
                    
                    if sb_data:
                        sb = self.utils.parse_superblock(sb_data)
                        
                        if sb and sb.is_valid():
                            partition_info = {
                                'offset': offset,
                                'superblock_offset': sb_offset,
                                'superblock': sb,
                                'block_size': sb.get_block_size(),
                                'total_size': sb.get_total_blocks() * sb.get_block_size(),
                                'start_sector': offset // 512,
                                'size_sectors': (sb.get_total_blocks() * sb.get_block_size()) // 512
                            }
                            
                            self.found_partitions.append(partition_info)
                            
                            print(f"    Block Size: {partition_info['block_size']} bytes")
                            print(f"    Total Size: {partition_info['total_size'] / 1024**3:.2f} GB")
                            print(f"    Start Sector: {partition_info['start_sector']}")
        
        print("\n\n" + "=" * 70)
        print(f"KET QUA: Tim thay {len(self.found_partitions)} EXT4 partition(s)")
        print("=" * 70)
        
        return len(self.found_partitions) > 0

    def print_partition_info(self):
        
        if not self.found_partitions:
            print("\nKhong co partition nao duoc tim thay!")
            return
        
        print("\n" + "=" * 70)
        print("THONG TIN CAC PARTITION TIM THAY")
        print("=" * 70)
        
        for i, part in enumerate(self.found_partitions):
            sb = part['superblock']
            
            print(f"\nPartition {i + 1}:")
            print("-" * 70)
            print(f"  Offset:          {part['offset']:,} bytes")
            print(f"  Start Sector:    {part['start_sector']:,}")
            print(f"  Size:            {part['total_size'] / 1024**3:.2f} GB ({part['size_sectors']:,} sectors)")
            print(f"  Block Size:      {part['block_size']} bytes")
            print(f"  Total Blocks:    {sb.get_total_blocks():,}")
            print(f"  Total Inodes:    {sb.s_inodes_count:,}")
            print(f"  Free Blocks:     {sb.s_free_blocks_count_lo:,}")
            print(f"  Free Inodes:     {sb.s_free_inodes_count:,}")
            print(f"  Filesystem ID:   {sb.s_uuid[:8].hex()}-...")

    def generate_partition_table_info(self):
        
        if not self.found_partitions:
            print("\nKhong co du lieu de tao partition table!")
            return
        
        print("\n" + "=" * 70)
        print("THONG TIN TAO LAI PARTITION TABLE")
        print("=" * 70)
        
        print("\nCac lenh fdisk/parted:")
        print("-" * 70)
        
        for i, part in enumerate(self.found_partitions):
            print(f"\nPartition {i + 1}:")
            print(f"  Start sector:  {part['start_sector']}")
            print(f"  End sector:    {part['start_sector'] + part['size_sectors'] - 1}")
            print(f"  Size (sectors): {part['size_sectors']}")
            print(f"  Type:          Linux (0x83)")
            print(f"\n  fdisk command:")
            print(f"    n  (new partition)")
            print(f"    p  (primary)")
            print(f"    {i + 1}  (partition number)")
            print(f"    {part['start_sector']}  (first sector)")
            print(f"    +{part['size_sectors']}  (last sector)")

    def export_partition_data(self, partition_index, output_file):
        
        if partition_index >= len(self.found_partitions):
            print(f"Loi: Partition index {partition_index} khong ton tai!")
            return False
        
        part = self.found_partitions[partition_index]
        
        print(f"\nDang xuat partition {partition_index + 1} ra file: {output_file}")
        print(f"Size: {part['total_size'] / 1024**3:.2f} GB")
        
        try:
            with open(self.device_path, 'rb') as src:
                src.seek(part['offset'])
                
                with open(output_file, 'wb') as dst:
                    remaining = part['total_size']
                    chunk_size = 1024 * 1024  # 1MB
                    
                    while remaining > 0:
                        read_size = min(chunk_size, remaining)
                        data = src.read(read_size)
                        
                        if not data:
                            break
                        
                        dst.write(data)
                        remaining -= len(data)
                        
                        # Progress
                        percent = ((part['total_size'] - remaining) / part['total_size']) * 100
                        print(f"  Tien do: {percent:.1f}%", end='\r')
            
            print(f"\n\nXuat thanh cong: {output_file}")
            return True
            
        except Exception as e:
            print(f"\nLoi khi xuat: {e}")
            return False
