#!/usr/bin/env python3
"""
Module: handlers.py
Chức năng: Các handler xử lý menu options
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))

from directory_scanner import DirectoryScanner
from bitmap_recovery import BitmapRecovery


def handle_check_data(image_file):
    """Option 1: Kiểm tra dữ liệu image"""
    print("\n" + "=" * 70)
    print("KIEM TRA DU LIEU IMAGE")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"\n❌ Loi: File khong ton tai: {image_file}")
        print("\n💡 Goi y: Chay 'sudo ./test_auto.sh' de tao image mau")
        return
    
    print(f"\n📁 File: {image_file}")
    print(f"📊 Size: {os.path.getsize(image_file):,} bytes ({os.path.getsize(image_file) / 1024**2:.2f} MB)")
    
    # Kiem tra filesystem
    print("\n🔍 Dang kiem tra filesystem...")
    
    scanner = DirectoryScanner(image_file)
    if not scanner.load_filesystem_info():
        print(" ❌ Loi: Khong the doc filesystem info!")
        return
    
    print(" ✓ Filesystem hop le!")
    
    sb = scanner.superblock
    print(f"\n📋 Thong tin filesystem:")
    print(f"   Block Size:        {sb.get_block_size()} bytes")
    print(f"   Total Blocks:      {sb.get_total_blocks():,}")
    print(f"   Total Inodes:      {sb.s_inodes_count:,}")
    print(f"   Inodes per Group:  {sb.s_inodes_per_group:,}")
    print(f"   Blocks per Group:  {sb.s_blocks_per_group:,}")
    
    # Check bitmap status
    print("\n🔍 Kiem tra bitmap status...")
    bitmap = BitmapRecovery(image_file)
    if bitmap.load_filesystem_info():
        # Check block bitmap
        block_bitmap = bitmap.read_block_bitmap(0)
        block_non_zero = sum(1 for b in block_bitmap if b != 0)
        block_total = len(block_bitmap)
        block_pct = (block_non_zero / block_total * 100) if block_total > 0 else 0
        
        # Check inode bitmap
        inode_bitmap = bitmap.read_inode_bitmap(0)
        inode_non_zero = sum(1 for b in inode_bitmap if b != 0)
        inode_total = len(inode_bitmap)
        inode_pct = (inode_non_zero / inode_total * 100) if inode_total > 0 else 0
        
        print(f"   Block Bitmap:  {block_non_zero}/{block_total} bytes ({block_pct:.1f}%)", end="")
        if block_pct < 1:
            print(" ❌ CORRUPT")
        elif block_pct < 5:
            print(" ⚠️  LOW")
        else:
            print(" ✅ OK")
        
        print(f"   Inode Bitmap:  {inode_non_zero}/{inode_total} bytes ({inode_pct:.1f}%)", end="")
        if inode_pct < 0.01:  # Nearly zero
            print(" ❌ CORRUPT")
        elif inode_pct < 3:
            print(" ⚠️  LOW")
        else:
            print(" ✅ OK")
    
    # Thu mount va xem du lieu
    print("\n🔍 Dang kiem tra du lieu...")
    
    loop_device = os.popen(f"losetup -f --show {image_file} 2>/dev/null").read().strip()
    if loop_device:
        mount_point = "/mnt/check_directory"
        os.makedirs(mount_point, exist_ok=True)
        
        ret = os.system(f"mount {loop_device} {mount_point} 2>/dev/null")
        if ret == 0:
            print(f"\n✅ Mount thanh cong!\n")
            print(f"📂 Noi dung:")
            os.system(f"tree -L 3 {mount_point} 2>/dev/null || find {mount_point} -type f | grep -v lost+found | sort")
            
            # Count files
            file_count = int(os.popen(f"find {mount_point} -type f 2>/dev/null | grep -v lost+found | wc -l").read().strip())
            dir_count = int(os.popen(f"find {mount_point} -type d 2>/dev/null | grep -v lost+found | wc -l").read().strip()) - 1
            print(f"\n📊 Thong ke: {file_count} files, {dir_count} directories")
            
            os.system(f"umount {mount_point}")
        else:
            print(f"\n❌ Khong the mount image! (Co the bi corrupt)")
        
        os.system(f"losetup -d {loop_device}")


def handle_corrupt_data(image_file):
    """Option 2: Phá hỏng directory/bitmap"""
    print("\n" + "=" * 70)
    print("PHA HONG DIRECTORY/BITMAP")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"\n❌ Loi: File khong ton tai: {image_file}")
        return False
    
    print("\n⚠️  CANH BAO: Thao tac nay se lam hong du lieu!")
    print("\nChon loai pha hong:")
    print("1. Pha hong block bitmap (group 0)")
    print("2. Pha hong inode bitmap (group 0)")
    print("3. Pha hong ca 2 bitmaps")
    print("0. Huy bo")
    
    try:
        choice = input("\n📝 Lua chon (0-3): ").strip()
    except EOFError:
        return False
    
    if choice == '0':
        print("\n✓ Da huy thao tac")
        return False
    
    bitmap = BitmapRecovery(image_file)
    if not bitmap.load_filesystem_info():
        print("❌ Loi: Khong the doc filesystem info!")
        return False
    
    corrupted = False
    
    if choice == '1':
        # Pha hong block bitmap
        print("\n💥 Dang pha hong block bitmap...")
        if bitmap.corrupt_block_bitmap(0):
            print("✓ Da ghi de block bitmap thanh zeros")
            
            # Verify corruption
            verify_bitmap = bitmap.read_block_bitmap(0)
            non_zero = sum(1 for b in verify_bitmap if b != 0)
            if non_zero == 0:
                print("✓ Xac nhan: Block bitmap = 0 (BI CORRUPT)")
                corrupted = True
            else:
                print(f"⚠️  Block bitmap con {non_zero} bytes khac 0")
    
    elif choice == '2':
        # Pha hong inode bitmap
        print("\n💥 Dang pha hong inode bitmap...")
        if bitmap.corrupt_inode_bitmap(0):
            print("✓ Da ghi de inode bitmap thanh zeros")
            
            # Verify corruption
            verify_bitmap = bitmap.read_inode_bitmap(0)
            non_zero = sum(1 for b in verify_bitmap if b != 0)
            if non_zero == 0:
                print("✓ Xac nhan: Inode bitmap = 0 (BI CORRUPT)")
                corrupted = True
            else:
                print(f"⚠️  Inode bitmap con {non_zero} bytes khac 0")
    
    elif choice == '3':
        # Pha hong ca 2
        print("\n💥 Dang pha hong block bitmap...")
        if bitmap.corrupt_block_bitmap(0):
            print("✓ Da ghi de block bitmap thanh zeros")
            verify_bitmap = bitmap.read_block_bitmap(0)
            non_zero = sum(1 for b in verify_bitmap if b != 0)
            if non_zero == 0:
                print("✓ Xac nhan: Block bitmap = 0 (BI CORRUPT)")
                corrupted = True
        
        print("\n💥 Dang pha hong inode bitmap...")
        if bitmap.corrupt_inode_bitmap(0):
            print("✓ Da ghi de inode bitmap thanh zeros")
            verify_bitmap = bitmap.read_inode_bitmap(0)
            non_zero = sum(1 for b in verify_bitmap if b != 0)
            if non_zero == 0:
                print("✓ Xac nhan: Inode bitmap = 0 (BI CORRUPT)")
                corrupted = True
    
    if corrupted:
        print("\n" + "=" * 70)
        print("⚠️  FILESYSTEM DA BI PHA HONG!")
        print("=" * 70)
        
        # Verify mount behavior
        print("\n🔍 Kiem tra xem filesystem co mount duoc khong...")
        os.system("losetup -D 2>/dev/null")
        loop_device = os.popen(f"losetup -f --show {image_file} 2>/dev/null").read().strip()
        can_mount = False
        
        if loop_device:
            mount_point = "/tmp/verify_corrupt"
            os.makedirs(mount_point, exist_ok=True)
            ret = os.system(f"mount {loop_device} {mount_point} 2>/dev/null")
            
            if ret == 0:
                can_mount = True
                file_count = int(os.popen(f"find {mount_point} -type f 2>/dev/null | grep -v lost+found | wc -l").read().strip())
                print(f"⚠️  Filesystem VAN CO THE mount (found {file_count} files)")
                print("   → EXT4 doc data truc tiep tu inodes, khong phu thuoc bitmap")
                os.system(f"umount {mount_point} 2>/dev/null")
            else:
                print("✓ Filesystem KHONG the mount")
            
            os.system(f"losetup -d {loop_device} 2>/dev/null")
        
        print("\n📝 Ghi chu:")
        print("  - Bitmap bi corrupt (tat ca = 0)")
        if can_mount:
            print("  - Nhung van mount duoc vi EXT4 doc data tu inodes")
        print("  - Bitmap chi dung de track blocks free/used")
        print("  - Khong the ghi file moi (khong biet block nao free)")
        print("\n💡 Dung option 3 de phuc hoi bitmap va restore chuc nang day du.")
    
    return corrupted


def handle_recover_data(image_file):
    """Option 3: Phục hồi directory/bitmap"""
    print("\n" + "=" * 70)
    print("PHUC HOI DIRECTORY/BITMAP")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"\n❌ Loi: File khong ton tai: {image_file}")
        return None
    
    print(f"\n📁 File: {image_file}")
    print(f"📊 Size: {os.path.getsize(image_file):,} bytes ({os.path.getsize(image_file) / 1024**2:.2f} MB)")
    
    # Buoc 1: Scan tat ca inodes
    print("\n" + "=" * 70)
    print("BUOC 1: QUET TAT CA INODES")
    print("=" * 70)
    
    scanner = DirectoryScanner(image_file)
    if not scanner.load_filesystem_info():
        print("❌ Loi: Khong the doc filesystem info!")
        return None
    
    if not scanner.scan_all_inodes():
        print("❌ Loi: Khong the quet inodes!")
        return None
    
    print(f"\n✓ Tim thay {len(scanner.found_inodes)} inodes:")
    dirs = sum(1 for i in scanner.found_inodes if i['is_dir'])
    files = sum(1 for i in scanner.found_inodes if i['is_file'])
    print(f"   📂 Directories: {dirs}")
    print(f"   📄 Files:       {files}")
    print(f"   🔧 Other:       {len(scanner.found_inodes) - dirs - files}")
    
    # Buoc 2: Rebuild directory tree
    print("\n" + "=" * 70)
    print("BUOC 2: XAY DUNG LAI CAY THU MUC")
    print("=" * 70)
    
    if scanner.rebuild_directory_tree():
        print("\n📂 Cau truc thu muc:")
        scanner.print_directory_tree()
        
        # Xuat file list
        output_file = image_file + ".recovered_files.txt"
        scanner.export_file_list(output_file)
        print(f"\n✓ Danh sach files da duoc xuat ra: {output_file}")
    
    # Buoc 3: Rebuild bitmaps
    print("\n" + "=" * 70)
    print("BUOC 3: XAY DUNG LAI BITMAPS")
    print("=" * 70)
    
    print("\n🔧 Se rebuild block bitmap va inode bitmap...")
    
    try:
        response = input("\nTiep tuc? (y/n): ").strip().lower()
    except EOFError:
        response = 'n'
    
    if response == 'y':
        bitmap = BitmapRecovery(image_file)
        if bitmap.load_filesystem_info():
            print("\n⏳ Dang rebuild block bitmap...")
            bitmap.rebuild_block_bitmap_from_inodes(scanner.found_inodes)
            
            print("\n⏳ Dang rebuild inode bitmap...")
            bitmap.rebuild_inode_bitmap_from_scan(scanner.found_inodes)
            
            print("\n" + "=" * 70)
            print("✅ PHUC HOI THANH CONG!")
            print("=" * 70)
            
            # Check bitmap accuracy
            print("\n📊 Kiem tra do chinh xac bitmap...")
            
            # Read rebuilt bitmaps
            block_bitmap = bitmap.read_block_bitmap(0)
            block_non_zero = sum(1 for b in block_bitmap if b != 0)
            block_pct = (block_non_zero / len(block_bitmap) * 100) if len(block_bitmap) > 0 else 0
            
            inode_bitmap = bitmap.read_inode_bitmap(0)
            inode_non_zero = sum(1 for b in inode_bitmap if b != 0)
            inode_pct = (inode_non_zero / len(inode_bitmap) * 100) if len(inode_bitmap) > 0 else 0
            
            print(f"   Block Bitmap: {block_non_zero}/{len(block_bitmap)} bytes ({block_pct:.1f}%) ✅")
            print(f"   Inode Bitmap: {inode_non_zero}/{len(inode_bitmap)} bytes ({inode_pct:.1f}%) ✅")
            
            # Verify mount
            print("\n🔍 Kiem tra filesystem...")
            os.system("losetup -D 2>/dev/null")
            loop_device = os.popen(f"losetup -f --show {image_file} 2>/dev/null").read().strip()
            if loop_device:
                mount_point = "/tmp/verify_recovery"
                os.makedirs(mount_point, exist_ok=True)
                ret = os.system(f"mount {loop_device} {mount_point} 2>/dev/null")
                if ret == 0:
                    file_count = int(os.popen(f"find {mount_point} -type f 2>/dev/null | grep -v lost+found | wc -l").read().strip())
                    print(f"✓ Mount thanh cong!")
                    print(f"✓ {file_count} files accessible")
                    print(f"✓ Filesystem hoat dong binh thuong")
                    os.system(f"umount {mount_point}")
                else:
                    print("⚠️  Filesystem van chua mount duoc")
                os.system(f"losetup -d {loop_device}")
            
            print("\n" + "=" * 70)
            print("📋 TOM TAT KET QUA")
            print("=" * 70)
            print(f"✅ Inodes recovered:     {len(scanner.found_inodes)}")
            print(f"✅ Directories rebuilt:  {sum(1 for i in scanner.found_inodes if i['is_dir'])}")
            print(f"✅ Files recovered:      {sum(1 for i in scanner.found_inodes if i['is_file'])}")
            print(f"✅ Block bitmap:         {block_pct:.1f}% restored")
            print(f"✅ Inode bitmap:         {inode_pct:.1f}% restored")
            print(f"✅ Filesystem status:    Mountable & Working")
            print("=" * 70)
        else:
            print("❌ Loi: Khong the doc filesystem info!")
    else:
        print("\n⚠️  Da bo qua rebuild bitmaps")
    
    return scanner


def handle_show_details(image_file):
    """Option 4: Xem thông tin chi tiết"""
    print("\n" + "=" * 70)
    print("THONG TIN CHI TIET")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f"\n❌ File khong ton tai: {image_file}")
        return
    
    print(f"\n📁 File: {image_file}")
    size = os.path.getsize(image_file)
    print(f"📊 Size: {size:,} bytes ({size / 1024**2:.2f} MB)")
    
    # Load filesystem info
    scanner = DirectoryScanner(image_file)
    if not scanner.load_filesystem_info():
        print("\n❌ Khong the doc filesystem info!")
        return
    
    sb = scanner.superblock
    
    print("\n" + "-" * 70)
    print("SUPERBLOCK INFORMATION")
    print("-" * 70)
    print(f"Block Size:          {sb.get_block_size()} bytes")
    print(f"Total Blocks:        {sb.get_total_blocks():,}")
    print(f"Free Blocks:         {sb.s_free_blocks_count_lo:,}")
    print(f"Used Blocks:         {sb.get_total_blocks() - sb.s_free_blocks_count_lo:,}")
    print(f"Total Inodes:        {sb.s_inodes_count:,}")
    print(f"Free Inodes:         {sb.s_free_inodes_count:,}")
    print(f"Used Inodes:         {sb.s_inodes_count - sb.s_free_inodes_count:,}")
    print(f"Inodes per Group:    {sb.s_inodes_per_group:,}")
    print(f"Blocks per Group:    {sb.s_blocks_per_group:,}")
    print(f"Inode Size:          {sb.s_inode_size} bytes")
    
    print("\n" + "-" * 70)
    print("GROUP DESCRIPTOR TABLE")
    print("-" * 70)
    print(f"Number of Groups:    {len(scanner.group_descriptors)}")
    
    for i, gd in enumerate(scanner.group_descriptors[:3]):  # Show first 3 groups
        print(f"\nGroup {i}:")
        print(f"  Block bitmap:      {gd.bg_block_bitmap_lo}")
        print(f"  Inode bitmap:      {gd.bg_inode_bitmap_lo}")
        print(f"  Inode table:       {gd.bg_inode_table_lo}")
        print(f"  Free blocks:       {gd.bg_free_blocks_count_lo}")
        print(f"  Free inodes:       {gd.bg_free_inodes_count_lo}")
    
    if len(scanner.group_descriptors) > 3:
        print(f"\n  ... and {len(scanner.group_descriptors) - 3} more groups")
