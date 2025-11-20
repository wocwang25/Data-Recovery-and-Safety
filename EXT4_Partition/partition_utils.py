#!/usr/bin/env python3

import os
import struct


def check_partition_table_valid(disk_image):
    
    if not os.path.exists(disk_image):
        return False
    
    try:
        with open(disk_image, 'rb') as f:
            mbr = f.read(512)
            
            # Check MBR signature (0x55AA at end)
            if len(mbr) >= 512 and mbr[510:512] == b'\x55\xaa':
                # Check if there's at least one partition entry
                partition_table = mbr[446:510]
                
                # Check if any partition entry is non-zero
                for i in range(4):
                    entry = partition_table[i*16:(i+1)*16]
                    if any(b != 0 for b in entry):
                        return True
                
        return False
    except:
        return False


def corrupt_partition_table(disk_image):
    
    if not os.path.exists(disk_image):
        print(f"Loi: File khong ton tai: {disk_image}")
        return False
    
    # Kiem tra truoc
    if not check_partition_table_valid(disk_image):
        print(" Partition table da bi hong tu truoc!")
        return False
    
    print(f"\n File: {disk_image}")
    print(f" Size: {os.path.getsize(disk_image):,} bytes")
    
    # Backup truoc khi pha
    backup_file = disk_image + ".backup_ptable"
    print(f"\n Dang tao backup -> {backup_file}")
    
    try:
        import shutil
        shutil.copy2(disk_image, backup_file)
        print(" Backup thanh cong!")
    except Exception as e:
        print(f" Loi khi backup: {e}")
        return False
    
    # Pha hong bang cach ghi 0 vao MBR
    print("\n Dang ghi de partition table...")
    
    try:
        with open(disk_image, 'r+b') as f:
            f.seek(0)
            f.write(b'\x00' * 512)  # Ghi 512 bytes 0
        
        print(" Da pha hong partition table!")
        
        # Verify
        if not check_partition_table_valid(disk_image):
            print(" Xac nhan: Partition table da bi hong!")
            print(f"\n De restore: cp {backup_file} {disk_image}")
            return True
        else:
            print(" La! Partition table van con hop le?")
            return False
            
    except Exception as e:
        print(f" Loi: {e}")
        return False


def rebuild_partition_table(disk_image, partitions):
    
    print("\n Dang tao lai partition table...")
    
    # Attach loop device
    loop_device = os.popen(f"losetup -f --show {disk_image}").read().strip()
    
    if not loop_device:
        print(" Loi: Khong the tao loop device!")
        return False
    
    print(f"   Loop device: {loop_device}")
    
    try:
        # Tao partition table moi
        print(" Dang tao MBR partition table...")
        ret = os.system(f"parted -s {loop_device} mklabel msdos 2>&1")
        
        if ret != 0:
            print(" Loi khi tao partition table!")
            return False
        
        # Tao lai cac partitions
        for i, part in enumerate(partitions):
            offset_mb = part['offset'] // (1024 * 1024)
            size_mb = part['total_size'] // (1024 * 1024)
            end_mb = offset_mb + size_mb
            
            print(f"\n Tao partition {i+1}:")
            print(f"   Start: {offset_mb} MB")
            print(f"   End: {end_mb} MB")
            print(f"   Size: {size_mb} MB")
            
            cmd = f"parted -s {loop_device} mkpart primary ext4 {offset_mb}MiB {end_mb}MiB"
            ret = os.system(f"{cmd} 2>&1")
            
            if ret != 0:
                print(f"   Canh bao: Co loi khi tao partition {i+1}")
        
        # Thong bao cho kernel
        print("\n Cap nhat kernel...")
        os.system(f"partprobe {loop_device}")
        os.system("sleep 1")
        
        return True
        
    finally:
        # Detach loop device
        os.system(f"losetup -d {loop_device}")
