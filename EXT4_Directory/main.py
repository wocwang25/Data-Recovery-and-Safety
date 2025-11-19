#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))

from directory_scanner import DirectoryScanner
from bitmap_recovery import BitmapRecovery
from ui import check_root, print_menu


def handle_check_data(image_file):
    
    print("\n" + "=" * 70)
    print("KIEM TRA DU LIEU TEST IMAGE")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"Loi: File khong ton tai: {image_file}")
        return
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes ({os.path.getsize(image_file) / 1024**2:.2f} MB)")
    
    # Kiem tra filesystem
    print("\n Dang kiem tra filesystem...")
    
    scanner = DirectoryScanner(image_file)
    if not scanner.load_filesystem_info():
        print(" Loi: Khong the doc filesystem info!")
        return
    
    print(" Filesystem hop le!")
    
    sb = scanner.superblock
    print(f"\n Thong tin filesystem:")
    print(f"   Block Size:        {sb.get_block_size()} bytes")
    print(f"   Total Blocks:      {sb.get_total_blocks():,}")
    print(f"   Total Inodes:      {sb.s_inodes_count:,}")
    print(f"   Inodes per Group:  {sb.s_inodes_per_group:,}")
    print(f"   Blocks per Group:  {sb.s_blocks_per_group:,}")
    
    # Thu mount va xem du lieu
    print("\n Dang kiem tra du lieu...")
    
    loop_device = os.popen(f"losetup -f --show {image_file}").read().strip()
    if loop_device:
        mount_point = "/mnt/check_directory"
        os.makedirs(mount_point, exist_ok=True)
        
        ret = os.system(f"mount {loop_device} {mount_point} 2>/dev/null")
        if ret == 0:
            print(f"\n Noi dung:")
            os.system(f"tree -L 2 {mount_point} 2>/dev/null || ls -lR {mount_point} | head -30")
            os.system(f"umount {mount_point}")
        else:
            print(f"\n Khong the mount image!")
        
        os.system(f"losetup -d {loop_device}")


def handle_corrupt_data(image_file):
    
    print("\n" + "=" * 70)
    print("PHA HONG DIRECTORY/BITMAP")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"Loi: File khong ton tai: {image_file}")
        return False
    
    print("\nChon loai pha hong:")
    print("1. Pha hong directory entries (root directory)")
    print("2. Pha hong block bitmap (group 0)")
    print("3. Pha hong inode bitmap (group 0)")
    print("4. Pha hong tat ca")
    
    try:
        choice = input("\n Lua chon (1-4): ").strip()
    except EOFError:
        return False
    
    bitmap = BitmapRecovery(image_file)
    if not bitmap.load_filesystem_info():
        print("Loi: Khong the doc filesystem info!")
        return False
    
    scanner = DirectoryScanner(image_file)
    if not scanner.load_filesystem_info():
        print("Loi: Khong the doc filesystem info!")
        return False
    
    corrupted = False
    
    if choice in ['1', '4']:
        # Pha hong root directory
        print("\n Dang pha hong root directory...")
        
        # Doc root inode (inode 2)
        root_inode = scanner.read_inode(2)
        if root_inode and root_inode.i_flags & 0x80000:
            # Parse extent
            extent_data = root_inode.i_block[12:24]  # First extent
            ee_start_hi = int.from_bytes(extent_data[6:8], 'little')
            ee_start_lo = int.from_bytes(extent_data[8:12], 'little')
            physical_block = (ee_start_hi << 32) | ee_start_lo
            
            block_size = scanner.superblock.get_block_size()
            dir_offset = physical_block * block_size
            
            # Backup
            backup_file = image_file + ".backup_root_dir"
            dir_data = scanner.utils.read_bytes(image_file, dir_offset, block_size)
            if dir_data:
                with open(backup_file, 'wb') as f:
                    f.write(dir_data)
                print(f"   Backup -> {backup_file}")
            
            # Ghi de
            with open(image_file, 'r+b') as f:
                f.seek(dir_offset)
                f.write(b'\x00' * block_size)
            
            print(" Da pha hong root directory!")
            corrupted = True
    
    if choice in ['2', '4']:
        if bitmap.corrupt_block_bitmap(0):
            corrupted = True
    
    if choice in ['3', '4']:
        if bitmap.corrupt_inode_bitmap(0):
            corrupted = True
    
    return corrupted


def handle_recover_data(image_file):
    
    print("\n" + "=" * 70)
    print("PHUC HOI DIRECTORY/BITMAP")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"Loi: File khong ton tai: {image_file}")
        return None
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Buoc 1: Scan tat ca inodes
    print("\n Buoc 1: Quet tat ca inodes")
    print("-" * 70)
    
    scanner = DirectoryScanner(image_file)
    if not scanner.load_filesystem_info():
        print("Loi: Khong the doc filesystem info!")
        return None
    
    if not scanner.scan_all_inodes():
        print("Loi: Khong the quet inodes!")
        return None
    
    print(f"\n Tim thay {len(scanner.found_inodes)} inodes:")
    dirs = sum(1 for i in scanner.found_inodes if i['is_dir'])
    files = sum(1 for i in scanner.found_inodes if i['is_file'])
    print(f"   Directories: {dirs}")
    print(f"   Files:       {files}")
    print(f"   Other:       {len(scanner.found_inodes) - dirs - files}")
    
    # Buoc 2: Rebuild directory tree
    print("\n Buoc 2: Xay dung lai cay thu muc")
    print("-" * 70)
    
    if scanner.rebuild_directory_tree():
        scanner.print_directory_tree()
        
        # Xuat file list
        output_file = image_file + ".recovered_files.txt"
        scanner.export_file_list(output_file)
    
    # Buoc 3: Rebuild bitmaps
    print("\n Buoc 3: Xay dung lai bitmaps")
    print("-" * 70)
    
    response = input("\n Ban co muon rebuild bitmaps? (y/n): ").strip().lower()
    
    if response == 'y':
        bitmap = BitmapRecovery(image_file)
        if bitmap.load_filesystem_info():
            # Rebuild block bitmap
            bitmap.rebuild_block_bitmap_from_inodes(scanner.found_inodes)
            
            # Rebuild inode bitmap
            bitmap.rebuild_inode_bitmap_from_scan(scanner.found_inodes)
            
            print("\n PHUC HOI THANH CONG!")
        else:
            print("Loi: Khong the doc filesystem info!")
    
    return scanner


def check_filesystem_status(image_file):
    
    if not os.path.exists(image_file):
        return False
    
    try:
        # Chi can mount duoc la OK
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


def main():
    check_root()
    
    # Lay image file tu argument hoac dung mac dinh
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
    else:
        image_file = "test_directory.img"
    
    # Kiem tra file ton tai
    if not os.path.exists(image_file):
        print(f" File khong ton tai: {image_file}")
        print(" Script se su dung file nay khi duoc tao.")
    
    # Kiem tra trang thai filesystem
    is_corrupted = not check_filesystem_status(image_file) if os.path.exists(image_file) else False
    scanner = None
    
    while True:
        print_menu(image_file, is_corrupted)
        
        try:
            choice = input("\n Nhap lua chon cua ban: ").strip()
            
            if choice == '0':
                print("\n" + "=" * 70)
                print(" CAM ON DA SU DUNG!")
                print("=" * 70)
                break
            
            elif choice == '1':
                # Kiem tra du lieu
                handle_check_data(image_file)
                # Cap nhat trang thai
                is_corrupted = not check_filesystem_status(image_file)
            
            elif choice == '2':
                # Pha hong
                if handle_corrupt_data(image_file):
                    is_corrupted = True
            
            elif choice == '3':
                # Phuc hoi
                scanner = handle_recover_data(image_file)
                if scanner:
                    is_corrupted = not check_filesystem_status(image_file)
            
            else:
                print("Loi: Lua chon khong hop le. Vui long chon 0-3.")
            
            try:
                input("\n  Nhan Enter de tiep tuc...")
            except EOFError:
                pass
            
        except KeyboardInterrupt:
            print("\n\n Tam biet!")
            break
        except EOFError:
            print("\n\n Tam biet!")
            break
        except Exception as e:
            print(f"\n Loi: {e}")
            import traceback
            traceback.print_exc()
            try:
                input("\n  Nhan Enter de tiep tuc...")
            except EOFError:
                pass


if __name__ == "__main__":
    main()
