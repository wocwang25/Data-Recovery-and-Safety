#!/usr/bin/env python3


import sys
import os
import struct
import shutil
from ext4_recovery import EXT4Recovery
from ext4_structures import *
from ext4_utils import EXT4Utils


def print_banner():
    
    print("\n" + "=" * 70)
    print("\nCÔNG CỤ PHỤC HỒI DỮ LIỆU EXT4 FILESYSTEM - Tham số sai của Volume")
    print("\t\tData Recovery and Safety - HCMUS")
    print("=" * 70)
    print()


def print_menu(image_file, is_corrupted):
    
    os.system('clear')
    print_banner()
    print("\t\t\tMENU CHÍNH")
    print("-" * 70)
    
    if image_file:
        status = " BỊ HỎNG" if is_corrupted else " HOẠT ĐỘNG"
        print(f" Image hiện tại: {os.path.basename(image_file)} - Trạng thái: {status}")
        print("-" * 70)
    
    print("1.  Kiểm tra dữ liệu test image")
    print("2.  Phá hỏng superblock")
    print("3.  Sửa chữa/Phục hồi superblock")
    print("0.  Thoát")
    print("-" * 70)


def check_superblock_valid(image_file):
    
    utils = EXT4Utils()
    data = utils.read_bytes(image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
    if not data:
        return False
    
    sb = utils.parse_superblock(data)
    return sb and sb.is_valid()


def mount_and_check_data(image_file, mount_point="/mnt/recovery_test"):
    
    print("\n" + "=" * 70)
    print(" KIỂM TRA DỮ LIỆU TEST IMAGE")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f" File không tồn tại: {image_file}")
        return False
    
    # Kiểm tra quyền root
    if os.geteuid() != 0:
        print("  Cảnh báo: Cần quyền root để mount filesystem!")
        print("   Chỉ có thể phân tích metadata...")
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Kiểm tra superblock có hợp lệ không
    print("\n Đang kiểm tra superblock...")
    
    utils = EXT4Utils()
    data = utils.read_bytes(image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
    
    if not data:
        print(" Không thể đọc superblock!")
        return False
    
    sb = utils.parse_superblock(data)
    
    if not sb or not sb.is_valid():
        print(" Superblock chính BỊ HỎNG!")
        print(" Vui lòng chọn option 3 để sửa chữa trước.")
        return False
    
    print(" Superblock hợp lệ!")
    
    # Hiển thị thông tin cơ bản
    print(f"\n Thông tin filesystem:")
    print(f"   Block Size:        {sb.get_block_size()} bytes")
    print(f"   Total Blocks:      {sb.get_total_blocks():,}")
    print(f"   Total Inodes:      {sb.s_inodes_count:,}")
    print(f"   Free Blocks:       {sb.s_free_blocks_count_lo:,}")
    
    # Thử mount và đọc dữ liệu
    if os.geteuid() == 0:
        print(f"\n Đang mount image vào {mount_point}...")
        os.makedirs(mount_point, exist_ok=True)
        
        ret = os.system(f"mount -o loop {image_file} {mount_point} 2>/dev/null")
        
        if ret == 0:
            print(" Mount thành công!")
            print(f"\n Nội dung filesystem:")
            os.system(f"ls -lah {mount_point} | head -20")
            
            # Đọc test file nếu có
            test_file = os.path.join(mount_point, "test_data.txt")
            if os.path.exists(test_file):
                print(f"\n Nội dung file test_data.txt:")
                with open(test_file, 'r') as f:
                    content = f.read().strip()
                    print(f"   >>> {content}")
            else:
                print(f"\n  File test_data.txt không tồn tại")
            
            os.system(f"umount {mount_point} 2>/dev/null")
            print(f"\n Đã unmount!")
            return True
        else:
            print(" Mount thất bại!")
            return False
    else:
        print("\n  Bỏ qua mount (cần quyền root)")
        return True


def corrupt_superblock(image_file):
    
    print("\n" + "=" * 70)
    print(" PHÁ HỎNG SUPERBLOCK")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f" File không tồn tại: {image_file}")
        return False
    
    # Kiểm tra trước
    if not check_superblock_valid(image_file):
        print("  Superblock đã bị hỏng từ trước!")
        return False
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Backup trước khi phá
    backup_file = image_file + ".backup"
    print(f"\n Đang tạo backup -> {backup_file}")
    
    try:
        shutil.copy2(image_file, backup_file)
        print(" Backup thành công!")
    except Exception as e:
        print(f" Lỗi khi backup: {e}")
        return False
    
    # Confirm
    print("\n  CẢNH BÁO: Sẽ ghi đè superblock chính bằng dữ liệu rác!")
    print("   (Backup đã được lưu)")
    response = input("\n Bạn có chắc chắn muốn phá hỏng? (y/n): ").strip().lower()
    
    if response != 'y':
        print(" Đã hủy.")
        return False
    
    # Phá hỏng bằng cách ghi 0 vào superblock
    print("\n Đang ghi đè superblock tại offset 1024...")
    
    try:
        with open(image_file, 'r+b') as f:
            f.seek(1024)
            f.write(b'\x00' * 100)  # Ghi 100 bytes 0
        
        print(" Đã phá hỏng superblock!")
        
        # Verify
        if not check_superblock_valid(image_file):
            print(" Xác nhận: Superblock đã bị hỏng!")
            print(f"\n Để restore: cp {backup_file} {image_file}")
            return True
        else:
            print("  Lạ! Superblock vẫn còn hợp lệ?")
            return False
            
    except Exception as e:
        print(f" Lỗi: {e}")
        return False


def recover_superblock(image_file, auto_mode=False):
    
    print("\n" + "=" * 70)
    print(" PHỤC HỒI SUPERBLOCK")
    print("=" * 70)
    
    if not os.path.exists(image_file):
        print(f" File không tồn tại: {image_file}")
        return False
    
    print(f"\n File: {image_file}")
    print(f" Size: {os.path.getsize(image_file):,} bytes")
    
    # Bước 1: Kiểm tra superblock chính
    print("\n" + "-" * 70)
    print("BƯỚC 1: Kiểm tra superblock chính")
    print("-" * 70)
    
    if check_superblock_valid(image_file):
        print(" Superblock chính vẫn còn tốt!")
        print("   Không cần phục hồi.")
        return True
    else:
        print(" Superblock chính bị hỏng!")
    
    # Bước 2: Tìm backup bằng EXT4Recovery class
    print("\n" + "-" * 70)
    print("BƯỚC 2: Tìm backup superblock")
    print("-" * 70)
    
    recovery = EXT4Recovery()
    utils = EXT4Utils()
    
    # Thử các block size
    backup_sb_data = None
    block_size_found = None
    
    for block_size in [4096, 2048, 1024]:
        print(f"\n  Thử block size = {block_size} bytes...")
        blocks_per_group = 8 * block_size
        
        for group_num in [1, 3, 5, 7, 9]:
            group_start_block = group_num * blocks_per_group
            
            if block_size == 1024:
                offset = group_start_block * block_size + 1024
            else:
                offset = group_start_block * block_size
            
            try:
                file_size = os.path.getsize(image_file)
                if offset + 1024 > file_size:
                    continue
            except:
                continue
            
            data = utils.read_bytes(image_file, offset, 1024)
            if data:
                sb = utils.parse_superblock(data)
                if sb and sb.is_valid():
                    backup_sb_data = data
                    block_size_found = block_size
                    print(f"   Tìm thấy backup tại group {group_num} (offset: {offset})")
                    break
        
        if backup_sb_data:
            break
    
    if not backup_sb_data:
        print("\n Không tìm thấy backup superblock nào!")
        return False
    
    # Bước 3: Khôi phục
    print("\n" + "-" * 70)
    print("BƯỚC 3: Khôi phục superblock chính")
    print("-" * 70)
    
    print(f"\n  Chuẩn bị ghi đè superblock chính bằng backup...")
    print(f"   Block size phát hiện: {block_size_found} bytes")
    
    if not auto_mode:
        response = input("\n Bạn có muốn tiếp tục? (y/n): ").strip().lower()
        
        if response != 'y':
            print(" Đã hủy.")
            return False
    else:
        print("\n Chế độ tự động: Tiến hành phục hồi...")
    
    # Backup trước khi sửa
    backup_file = image_file + ".before_recovery"
    print(f"\n Đang backup file gốc -> {backup_file}")
    
    try:
        shutil.copy2(image_file, backup_file)
        print(" Đã backup!")
    except Exception as e:
        print(f"  Không thể backup: {e}")
        if not auto_mode:
            response = input("   Tiếp tục không có backup? (y/n): ").strip().lower()
            if response != 'y':
                print(" Đã hủy.")
                return False
    
    # Ghi đè superblock
    print("\n Đang ghi superblock...")
    
    try:
        with open(image_file, 'r+b') as f:
            f.seek(1024)
            f.write(backup_sb_data)
        
        print("\n" + "=" * 70)
        print(" PHỤC HỒI THÀNH CÔNG! ")
        print("=" * 70)
        print(f"\n File đã được sửa: {image_file}")
        print(f" Backup gốc: {backup_file}")
        print("\n Filesystem đã được khôi phục!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n Phục hồi thất bại: {e}")
        return False





def main():
    
    print_banner()
    
    # Lấy image file và auto mode từ arguments
    image_file = "test_image_1gb.img"
    auto_recover = False
    
    if len(sys.argv) > 1:
        image_file = sys.argv[1]
    
    if len(sys.argv) > 2 and sys.argv[2] == "--auto-recover":
        auto_recover = True
    
    # Kiểm tra file tồn tại
    if not os.path.exists(image_file):
        print(f"  File không tồn tại: {image_file}")
        if not auto_recover:
            print(" Script sẽ sử dụng file này khi được tạo.")
        else:
            sys.exit(1)
    
    is_corrupted = not check_superblock_valid(image_file) if os.path.exists(image_file) else False
    
    # Nếu auto mode, chỉ recover và thoát
    if auto_recover:
        if is_corrupted:
            print("\n Chế độ tự động: Phục hồi superblock...")
            if recover_superblock(image_file, auto_mode=True):
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("\n Superblock đã hoạt động bình thường!")
            sys.exit(0)
    
    # Main loop
    while True:
        print_menu(image_file, is_corrupted)
        
        try:
            choice = input("\n Nhập lựa chọn của bạn: ").strip()
            
            if choice == '0':
                print("\n" + "=" * 70)
                print("\t\t\tCẢM ƠN ĐÃ SỬ DỤNG!")
                print("=" * 70)
                break
            
            elif choice == '1':
                # Kiểm tra dữ liệu
                mount_and_check_data(image_file)
                # Cập nhật trạng thái
                is_corrupted = not check_superblock_valid(image_file)
            
            elif choice == '2':
                # Phá hỏng
                if corrupt_superblock(image_file):
                    is_corrupted = True
            
            elif choice == '3':
                # Sửa chữa
                if recover_superblock(image_file, auto_mode=False):
                    is_corrupted = False
            
            else:
                print(" Lựa chọn không hợp lệ. Vui lòng chọn 0-3.")
            
            try:
                input("\n⏸  Nhấn Enter để tiếp tục...")
            except EOFError:
                pass
            print("\n" * 2)  # Clear screen effect
            
        except KeyboardInterrupt:
            print("\n\n Tạm biệt!")
            break
        except EOFError:
            print("\n\n Tạm biệt!")
            break
        except Exception as e:
            print(f"\n Lỗi: {e}")
            import traceback
            traceback.print_exc()
            try:
                input("\n⏸  Nhấn Enter để tiếp tục...")
            except EOFError:
                pass


if __name__ == "__main__":
    main()
