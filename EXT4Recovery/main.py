#!/usr/bin/env python3
"""
EXT4 Data Recovery Tool
Main program - Giao diện chính của công cụ phục hồi dữ liệu EXT4
Tương tự như main.cpp trong FileSystem project

Author: Your Name
Date: 2025
"""

import sys
import os
from ext4_recovery import EXT4Recovery
from ext4_structures import *


def print_banner():
    """In banner chương trình"""
    print("\n" + "=" * 60)
    print("  _____ _  _ _____ _  _   ____  ___  __  __  __  ___  ____  _  _ ")
    print(" | ____| \\/ |_   _| || | |  _ \\| __||  \\/  |/ _ \\| _ \\| __|| \\/ |")
    print(" |  _| |    | | | | || |_| (_) | _| | |\\/| | ( ) |   /| _| |    |")
    print(" |____||_||_| |_| |__   _|____/|___||_|  |_|\\___/|_|_\\|___||_||_|")
    print("                     |_|                                          ")
    print("\n  🛠️  CÔNG CỤ PHỤC HỒI DỮ LIỆU EXT4 FILESYSTEM")
    print("=" * 60)
    print()


def print_menu():
    """In menu chính"""
    print("\n" + "-" * 60)
    print("📋 MENU CHÍNH")
    print("-" * 60)
    print("1. Mở device/image file")
    print("2. Hiển thị thông tin superblock")
    print("3. Tìm và hiển thị backup superblocks")
    print("4. Đọc group descriptors")
    print("5. Liệt kê thư mục root")
    print("6. Đọc inode cụ thể")
    print("7. Phục hồi file từ inode")
    print("8. Quét tìm inodes (khi metadata bị hỏng)")
    print("9. Tạo báo cáo phục hồi")
    print("0. Thoát")
    print("-" * 60)


def handle_open_device(recovery: EXT4Recovery) -> bool:
    """Xử lý mở device"""
    print("\n📂 MỞ DEVICE/IMAGE FILE")
    print("-" * 60)
    
    path = input("Nhập đường dẫn đến device/image file: ").strip()
    
    if not path:
        print("❌ Đường dẫn không hợp lệ")
        return False
    
    # Kiểm tra quyền truy cập
    if not os.path.exists(path):
        print(f"❌ File không tồn tại: {path}")
        return False
    
    # Thử mở device
    return recovery.open_device(path)


def handle_show_superblock(recovery: EXT4Recovery):
    """Hiển thị thông tin superblock"""
    if not recovery.superblock:
        print("❌ Chưa mở device hoặc superblock không hợp lệ")
        return
    
    recovery.print_superblock_info()


def handle_find_backups(recovery: EXT4Recovery):
    """Tìm backup superblocks"""
    if not recovery.device_path:
        print("❌ Chưa mở device")
        return
    
    print("\n🔍 TÌM BACKUP SUPERBLOCKS")
    print("-" * 60)
    
    if recovery.find_backup_superblocks():
        print(f"\n✅ Tìm thấy {len(recovery.backup_superblocks)} backup(s):")
        for group_num, sb in recovery.backup_superblocks:
            print(f"\n  📍 Backup tại Group {group_num}:")
            print(f"     Block Size: {sb.get_block_size()} bytes")
            print(f"     Total Blocks: {sb.get_total_blocks():,}")
            print(f"     Total Inodes: {sb.s_inodes_count:,}")
            print(f"     Magic: 0x{sb.s_magic:04X}")
    else:
        print("❌ Không tìm thấy backup nào")


def handle_read_group_descriptors(recovery: EXT4Recovery):
    """Đọc group descriptors"""
    if not recovery.superblock:
        print("❌ Chưa có superblock hợp lệ")
        return
    
    if recovery.read_group_descriptors():
        print(f"\n✅ Đã đọc {len(recovery.group_descriptors)} group descriptors")
        
        # Hiển thị thông tin một vài groups đầu
        show_count = min(5, len(recovery.group_descriptors))
        print(f"\n📋 Thông tin {show_count} groups đầu tiên:")
        
        for i in range(show_count):
            gd = recovery.group_descriptors[i]
            print(f"\n  Group {i}:")
            print(f"    Block Bitmap:    Block {gd.get_block_bitmap()}")
            print(f"    Inode Bitmap:    Block {gd.get_inode_bitmap()}")
            print(f"    Inode Table:     Block {gd.get_inode_table()}")
            print(f"    Free Blocks:     {gd.bg_free_blocks_count_lo}")
            print(f"    Free Inodes:     {gd.bg_free_inodes_count_lo}")
            print(f"    Used Directories: {gd.bg_used_dirs_count_lo}")


def handle_list_root_directory(recovery: EXT4Recovery):
    """Liệt kê thư mục root"""
    if not recovery.superblock or not recovery.group_descriptors:
        print("❌ Chưa đọc đầy đủ metadata")
        return
    
    print("\n📁 NỘI DUNG THƯ MỤC ROOT (Inode 2)")
    print("-" * 60)
    
    entries = recovery.list_directory(2)
    
    if not entries:
        print("❌ Không thể đọc directory hoặc directory rỗng")
        return
    
    print(f"\nTìm thấy {len(entries)} entries:\n")
    print(f"{'Inode':<10} {'Type':<15} {'Name':<30}")
    print("-" * 60)
    
    for entry in entries:
        print(f"{entry.inode:<10} {entry.get_type_name():<15} {entry.name:<30}")


def handle_read_inode(recovery: EXT4Recovery):
    """Đọc inode cụ thể"""
    if not recovery.superblock or not recovery.group_descriptors:
        print("❌ Chưa đọc đầy đủ metadata")
        return
    
    print("\n📄 ĐỌC INODE")
    print("-" * 60)
    
    try:
        inode_num = int(input("Nhập số inode cần đọc: "))
    except ValueError:
        print("❌ Số inode không hợp lệ")
        return
    
    inode = recovery.read_inode(inode_num)
    
    if not inode:
        print(f"❌ Không thể đọc inode {inode_num}")
        return
    
    print(f"\n✅ Thông tin Inode {inode_num}:")
    print("-" * 60)
    print(f"Mode:          0o{inode.i_mode:o}")
    print(f"UID:           {inode.i_uid}")
    print(f"GID:           {inode.i_gid}")
    print(f"Size:          {recovery.utils.format_bytes(inode.get_size())}")
    print(f"Links Count:   {inode.i_links_count}")
    print(f"Blocks:        {inode.i_blocks_lo}")
    print(f"Flags:         0x{inode.i_flags:08X}")
    
    # Type
    if inode.is_directory():
        print(f"Type:          Directory")
    elif inode.is_regular_file():
        print(f"Type:          Regular File")
    elif inode.is_symlink():
        print(f"Type:          Symbolic Link")
    else:
        print(f"Type:          Other")
    
    # Times
    from datetime import datetime
    if inode.i_atime > 0:
        print(f"Access Time:   {datetime.fromtimestamp(inode.i_atime)}")
    if inode.i_mtime > 0:
        print(f"Modify Time:   {datetime.fromtimestamp(inode.i_mtime)}")
    if inode.i_ctime > 0:
        print(f"Change Time:   {datetime.fromtimestamp(inode.i_ctime)}")
    
    # Data blocks
    if inode.i_flags & EXT4_EXTENTS_FL:
        print(f"\nData:          Sử dụng Extents")
    else:
        print(f"\nDirect Blocks:")
        for i in range(12):
            if inode.i_block[i] != 0:
                print(f"  Block {i}: {inode.i_block[i]}")


def handle_recover_file(recovery: EXT4Recovery):
    """Phục hồi file"""
    if not recovery.superblock or not recovery.group_descriptors:
        print("❌ Chưa đọc đầy đủ metadata")
        return
    
    print("\n💾 PHỤC HỒI FILE")
    print("-" * 60)
    
    try:
        inode_num = int(input("Nhập số inode của file cần phục hồi: "))
    except ValueError:
        print("❌ Số inode không hợp lệ")
        return
    
    output_path = input("Nhập đường dẫn lưu file (ví dụ: recovered_file.txt): ").strip()
    
    if not output_path:
        print("❌ Đường dẫn không hợp lệ")
        return
    
    recovery.recover_file(inode_num, output_path)


def handle_scan_inodes(recovery: EXT4Recovery):
    """Quét tìm inodes"""
    if not recovery.device_path or not recovery.block_size:
        print("❌ Chưa mở device hoặc chưa xác định được block size")
        return
    
    print("\n🔍 QUÉT TÌM INODES")
    print("-" * 60)
    
    try:
        start_block = int(input("Nhập block bắt đầu quét (0 = bắt đầu): ") or "0")
        num_blocks = int(input("Nhập số blocks cần quét (100 = mặc định): ") or "100")
    except ValueError:
        print("❌ Giá trị không hợp lệ")
        return
    
    inodes = recovery.scan_for_inodes(start_block, num_blocks)
    
    if inodes:
        print(f"\n✅ Tìm thấy {len(inodes)} inodes:")
        for i, inode_num in enumerate(inodes[:20]):  # Hiển thị 20 inodes đầu
            print(f"  {i+1}. Inode {inode_num}")
        
        if len(inodes) > 20:
            print(f"  ... và {len(inodes) - 20} inodes khác")


def handle_generate_report(recovery: EXT4Recovery):
    """Tạo báo cáo"""
    if not recovery.device_path:
        print("❌ Chưa mở device")
        return
    
    print("\n📝 TẠO BÁO CÁO PHỤC HỒI")
    print("-" * 60)
    
    report = recovery.generate_recovery_report()
    print(report)
    
    # Hỏi có muốn lưu vào file không
    save = input("\nBạn có muốn lưu báo cáo vào file? (y/n): ").strip().lower()
    
    if save == 'y':
        filename = input("Nhập tên file (mặc định: recovery_report.txt): ").strip()
        if not filename:
            filename = "recovery_report.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ Đã lưu báo cáo vào {filename}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu file: {e}")


def main():
    """Hàm main"""
    print_banner()
    
    recovery = EXT4Recovery()
    
    # Main loop
    while True:
        print_menu()
        
        try:
            choice = input("\n👉 Nhập lựa chọn của bạn: ").strip()
            
            if choice == '0':
                print("\n👋 Tạm biệt!")
                break
            
            elif choice == '1':
                handle_open_device(recovery)
            
            elif choice == '2':
                handle_show_superblock(recovery)
            
            elif choice == '3':
                handle_find_backups(recovery)
            
            elif choice == '4':
                handle_read_group_descriptors(recovery)
            
            elif choice == '5':
                handle_list_root_directory(recovery)
            
            elif choice == '6':
                handle_read_inode(recovery)
            
            elif choice == '7':
                handle_recover_file(recovery)
            
            elif choice == '8':
                handle_scan_inodes(recovery)
            
            elif choice == '9':
                handle_generate_report(recovery)
            
            else:
                print("❌ Lựa chọn không hợp lệ")
            
            input("\n⏸️  Nhấn Enter để tiếp tục...")
            print("\n" * 2)  # Clear screen effect
            
        except KeyboardInterrupt:
            print("\n\n👋 Tạm biệt!")
            break
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
