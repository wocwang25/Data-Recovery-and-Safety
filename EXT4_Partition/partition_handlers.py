#!/usr/bin/env python3

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from partition_scanner import PartitionScanner
from partition_utils import check_partition_table_valid, corrupt_partition_table, rebuild_partition_table


def handle_check_data(disk_image):
    
    print("\n" + "=" * 70)
    print("KIEM TRA PARTITION TABLE VA DU LIEU")
    print("=" * 70)
    
    if not os.path.exists(disk_image):
        print(f"Loi: File khong ton tai: {disk_image}")
        return
    
    print(f"\n File: {disk_image}")
    print(f" Size: {os.path.getsize(disk_image):,} bytes ({os.path.getsize(disk_image) / 1024**3:.2f} GB)")
    
    # Kiem tra partition table
    print("\n Dang kiem tra partition table...")
    
    if check_partition_table_valid(disk_image):
        print(" Partition table HOP LE!")
        
        # Hien thi thong tin partition
        print("\n Thong tin partitions:")
        os.system(f"fdisk -l {disk_image} 2>/dev/null | grep -E 'Disk|Device|{disk_image}'")
        
        # Thu mount partitions
        print("\n Dang kiem tra du lieu tren partitions...")
        
        loop_device = os.popen(f"losetup -f --show {disk_image}").read().strip()
        if loop_device:
            os.system(f"partprobe {loop_device}")
            os.system("sleep 1")
            
            # Kiem tra partition 1
            if os.path.exists(f"{loop_device}p1"):
                mount_point = "/mnt/check_part1"
                os.makedirs(mount_point, exist_ok=True)
                
                ret = os.system(f"mount {loop_device}p1 {mount_point} 2>/dev/null")
                if ret == 0:
                    print(f"\n Partition 1 - Noi dung:")
                    os.system(f"ls -lah {mount_point} | head -15")
                    os.system(f"umount {mount_point}")
                else:
                    print(f"\n Partition 1 - Khong the mount")
            
            # Kiem tra partition 2
            if os.path.exists(f"{loop_device}p2"):
                mount_point = "/mnt/check_part2"
                os.makedirs(mount_point, exist_ok=True)
                
                ret = os.system(f"mount {loop_device}p2 {mount_point} 2>/dev/null")
                if ret == 0:
                    print(f"\n Partition 2 - Noi dung:")
                    os.system(f"ls -lah {mount_point} | head -15")
                    os.system(f"umount {mount_point}")
                else:
                    print(f"\n Partition 2 - Khong the mount")
            
            os.system(f"losetup -d {loop_device}")
    else:
        print(" Partition table BI HONG hoac khong ton tai!")
        print(" Vui long chon option 3 de quet lai partitions.")


def handle_corrupt_partition_table(disk_image):
    
    print("\n" + "=" * 70)
    print("PHA HONG PARTITION TABLE")
    print("=" * 70)
    
    # Confirm
    print("\n CANH BAO: Se ghi de partition table (512 bytes dau)!")
    print("   (Backup se duoc tu dong tao)")
    response = input("\n Ban co chac chan muon pha hong? (y/n): ").strip().lower()
    
    if response != 'y':
        print(" Da huy.")
        return False
    
    return corrupt_partition_table(disk_image)


def handle_scan_and_recover(disk_image):
    
    print("\n" + "=" * 70)
    print("QUET VA PHUC HOI PARTITIONS")
    print("=" * 70)
    
    if not os.path.exists(disk_image):
        print(f"Loi: File khong ton tai: {disk_image}")
        return None
    
    print(f"\n File: {disk_image}")
    print(f" Size: {os.path.getsize(disk_image):,} bytes ({os.path.getsize(disk_image) / 1024**3:.2f} GB)")
    
    # Kiem tra partition table
    print("\n Buoc 1: Kiem tra partition table hien tai")
    print("-" * 70)
    
    if check_partition_table_valid(disk_image):
        print(" Partition table van con tot!")
        print("   Khong can phuc hoi.")
        return None
    else:
        print(" Partition table bi hong!")
    
    # Quet tim partitions
    print("\n Buoc 2: Quet disk tim EXT4 partitions")
    print("-" * 70)
    
    scanner = PartitionScanner(disk_image)
    
    max_scan_gb = int(os.path.getsize(disk_image) / 1024**3) + 1
    
    if scanner.scan_for_ext4(max_scan_gb):
        print("\n Buoc 3: Thong tin partitions tim thay")
        print("-" * 70)
        scanner.print_partition_info()
        
        print("\n Buoc 4: Thong tin tao lai partition table")
        print("-" * 70)
        scanner.generate_partition_table_info()
        
        # Rebuild partition table
        print("\n Buoc 5: Khoi phuc partition table")
        print("-" * 70)
        
        response = input("\n Ban co muon tu dong tao lai partition table? (y/n): ").strip().lower()
        
        if response == 'y':
            if rebuild_partition_table(disk_image, scanner.found_partitions):
                print("\n PHUC HOI THANH CONG!")
                print(" Partition table da duoc tao lai!")
                
                # Verify
                print("\n Xac nhan partition table:")
                os.system(f"fdisk -l {disk_image} | grep -E 'Device|{disk_image}'")
            else:
                print("\n PHUC HOI THAT BAI!")
            
            return scanner
        else:
            print("\n Da huy - Ban co the tao lai thu cong:")
            print(" Ban co the su dung fdisk/parted de tao lai partition table")
            
            return scanner
    else:
        print("\n Khong tim thay partition nao!")
        return None
