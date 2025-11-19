#!/usr/bin/env python3


import os


print("=" * 60)
print(" TẠO EXT4 TEST IMAGE")
print("=" * 60)

# Cấu hình
IMAGE_FILE = "test_ext4.img"
IMAGE_SIZE_MB = 1000
MOUNT_POINT = "/mnt/ext4_test"

# Bước 1: Tạo file image
print(f"\n[1/6] Tạo file {IMAGE_FILE} ({IMAGE_SIZE_MB}MB)...")
os.system(f"dd if=/dev/zero of={IMAGE_FILE} bs=1M count={IMAGE_SIZE_MB} 2>/dev/null")
print(" Done")

# Bước 2: Format EXT4
print(f"\n[2/6] Format EXT4...")
os.system(f"mkfs.ext4 -F {IMAGE_FILE} >/dev/null 2>&1")
print(" Done")

# Bước 3: Mount
print(f"\n[3/6] Mount...")
os.makedirs(MOUNT_POINT, exist_ok=True)
os.system(f"mount -o loop {IMAGE_FILE} {MOUNT_POINT}")
print(" Done")

# Bước 4: Tạo test files
print(f"\n[4/6] Tạo test files...")
os.system(f"echo 'Hello World from EXT4!' > {MOUNT_POINT}/test.txt")
os.system(f"echo 'Document content here' > {MOUNT_POINT}/document.txt")
os.system(f"mkdir -p {MOUNT_POINT}/folder")
os.system(f"echo 'Nested file' > {MOUNT_POINT}/folder/nested.txt")
print(" Done")

# Bước 5: Unmount
print(f"\n[5/6] Unmount...")
os.system(f"umount {MOUNT_POINT}")
print(" Done")

# Bước 6: Làm hỏng superblock
print(f"\n[6/6] Làm hỏng superblock (để test recovery)...")
response = input("Làm hỏng superblock ngay? (y/n): ").strip().lower()

if response == 'y':
    # Backup trước
    os.system(f"cp {IMAGE_FILE} {IMAGE_FILE}.backup")
    # Ghi đè superblock tại offset 1024
    os.system(f"dd if=/dev/zero of={IMAGE_FILE} bs=1024 count=1 seek=1 conv=notrunc 2>/dev/null")
    print(" Đã làm hỏng superblock!")
    print(f"   Backup lưu tại: {IMAGE_FILE}.backup")
else:
    print("⏭  Bỏ qua")

# Kết quả
print("\n" + "=" * 60)
print(" HOÀN TẤT!")
print("=" * 60)
print(f"\n File: {os.path.abspath(IMAGE_FILE)}")
print(f"\n Test recovery:")
print(f"   python3 main.py")
print(f"   → Chọn option 1, mở: {IMAGE_FILE}")
print(f"   → Tool sẽ tự động tìm backup superblock")
print(f"\n Để restore:")
print(f"   cp {IMAGE_FILE}.backup {IMAGE_FILE}")
print("=" * 60)
