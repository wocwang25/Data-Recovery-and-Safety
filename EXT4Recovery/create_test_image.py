#!/usr/bin/env python3
"""
Example script: Tạo test EXT4 image và làm hỏng superblock
Sử dụng để test khả năng phục hồi
"""

import os
import sys


def create_test_image():
    """Tạo một test image để thử nghiệm"""
    print("🔧 TẠO TEST IMAGE")
    print("=" * 60)
    
    filename = "test_ext4.img"
    size_mb = 100
    
    print(f"\n📝 Tạo file image: {filename} ({size_mb}MB)")
    
    # Tạo file rỗng
    with open(filename, 'wb') as f:
        f.write(b'\x00' * (size_mb * 1024 * 1024))
    
    print(f"✅ Đã tạo {filename}")
    print("\n⚠️  Tiếp theo, bạn cần:")
    print("   1. Format file thành EXT4:")
    print(f"      Linux: sudo mkfs.ext4 {filename}")
    print(f"      macOS: brew install e2fsprogs; sudo $(brew --prefix e2fsprogs)/sbin/mkfs.ext4 {filename}")
    print("\n   2. Mount và thêm dữ liệu test:")
    print(f"      sudo mount -o loop {filename} /mnt")
    print("      sudo cp test_files/* /mnt/")
    print("      sudo umount /mnt")
    print("\n   3. Làm hỏng superblock (để test recovery):")
    print(f"      dd if=/dev/zero of={filename} bs=1024 count=1 seek=1 conv=notrunc")
    print("\n   4. Test recovery:")
    print("      python main.py")


def corrupt_superblock():
    """Làm hỏng superblock của image có sẵn"""
    print("\n⚠️  LÀM HỎNG SUPERBLOCK")
    print("=" * 60)
    
    filename = input("Nhập tên file image: ").strip()
    
    if not os.path.exists(filename):
        print(f"❌ File không tồn tại: {filename}")
        return
    
    confirm = input(f"⚠️  Bạn chắc chắn muốn làm hỏng superblock của {filename}? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Hủy bỏ")
        return
    
    try:
        # Ghi 0 lên superblock tại offset 1024
        with open(filename, 'r+b') as f:
            f.seek(1024)
            f.write(b'\x00' * 1024)
        
        print(f"✅ Đã làm hỏng superblock của {filename}")
        print("   Bây giờ bạn có thể test recovery bằng python main.py")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")


def main():
    print("\n🧪 CÔNG CỤ TẠO TEST IMAGE")
    print("=" * 60)
    print("1. Tạo test image mới")
    print("2. Làm hỏng superblock (để test recovery)")
    print("0. Thoát")
    
    choice = input("\nNhập lựa chọn: ").strip()
    
    if choice == '1':
        create_test_image()
    elif choice == '2':
        corrupt_superblock()
    else:
        print("Thoát")


if __name__ == "__main__":
    main()
