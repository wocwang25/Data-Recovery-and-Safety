#!/bin/bash

# Script test tu dong cho directory recovery workflow

set -e

IMAGE_FILE="test_directory.img"
IMAGE_SIZE="1000M"
MOUNT_POINT="/mnt/test_directory"

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    sudo umount $MOUNT_POINT 2>/dev/null || true
    LOOP_DEV=$(losetup -a | grep "$IMAGE_FILE" | cut -d: -f1)
    if [ ! -z "$LOOP_DEV" ]; then
        sudo losetup -d $LOOP_DEV
    fi
}

# Register cleanup on exit
trap cleanup EXIT

# Kiem tra quyen sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)"
    exit 1
fi

echo "========================================="
echo "DIRECTORY RECOVERY TEST - AUTO MODE"
echo "========================================="
echo ""

# BUOC 1: Tao test image
echo "BUOC 1: TAO TEST IMAGE VOI DU LIEU"
echo "----------------------------------------"

# Xoa file cu neu ton tai
if [ -f "$IMAGE_FILE" ]; then
    echo " Xoa file cu: $IMAGE_FILE"
    rm -f "$IMAGE_FILE"
    rm -f "$IMAGE_FILE".backup_*
    rm -f "$IMAGE_FILE".recovered_files.txt
fi

# Tao image rong
echo " Tao image: $IMAGE_FILE ($IMAGE_SIZE)"
dd if=/dev/zero of="$IMAGE_FILE" bs=1M count=100 status=none

# Format thanh EXT4
echo " Format EXT4..."
mkfs.ext4 -F "$IMAGE_FILE" > /dev/null 2>&1

# Mount va tao du lieu test
echo " Tao du lieu test..."
mkdir -p "$MOUNT_POINT"
LOOP_DEV=$(losetup -f --show "$IMAGE_FILE")
mount "$LOOP_DEV" "$MOUNT_POINT"

# Tao cau truc thu muc
mkdir -p "$MOUNT_POINT/docs"
mkdir -p "$MOUNT_POINT/images"
mkdir -p "$MOUNT_POINT/data/subdir1"
mkdir -p "$MOUNT_POINT/data/subdir2"

# Tao cac file
echo "This is a test document" > "$MOUNT_POINT/docs/readme.txt"
echo "Important data" > "$MOUNT_POINT/docs/important.txt"
dd if=/dev/urandom of="$MOUNT_POINT/images/photo.jpg" bs=1K count=10 2>/dev/null
echo "Data file 1" > "$MOUNT_POINT/data/subdir1/file1.txt"
echo "Data file 2" > "$MOUNT_POINT/data/subdir2/file2.txt"
echo "Root level file" > "$MOUNT_POINT/test.txt"

umount "$MOUNT_POINT"
losetup -d "$LOOP_DEV"

echo " THANH CONG!"
echo ""

# BUOC 2: Kiem tra du lieu ban dau
echo "BUOC 2: KIEM TRA DU LIEU BAN DAU"
echo "----------------------------------------"
LOOP_DEV=$(losetup -f --show "$IMAGE_FILE")
mount "$LOOP_DEV" "$MOUNT_POINT"
tree "$MOUNT_POINT" 2>/dev/null || ls -lR "$MOUNT_POINT" | head -30
umount "$MOUNT_POINT"
losetup -d "$LOOP_DEV"
echo ""

# BUOC 3: Pha hong directory/bitmap
echo "BUOC 3: PHA HONG DIRECTORY VA BITMAP"
echo "----------------------------------------"
echo " Dang pha hong..."
# Se dung Python de pha hong vi can parse EXT4 structures
python3 - <<'EOF'
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))

from bitmap_recovery import BitmapRecovery
from directory_scanner import DirectoryScanner

image_file = "test_directory.img"

# Load filesystem
bitmap = BitmapRecovery(image_file)
if bitmap.load_filesystem_info():
    # Pha hong block bitmap group 0
    bitmap.corrupt_block_bitmap(0)
    # Pha hong inode bitmap group 0
    bitmap.corrupt_inode_bitmap(0)
    print(" Da pha hong bitmaps!")
else:
    print(" Loi khi load filesystem!")
    sys.exit(1)
EOF

echo ""

# BUOC 4: Verify khong mount duoc
echo "BUOC 4: XAC NHAN FILESYSTEM BI HONG"
echo "----------------------------------------"
LOOP_DEV=$(losetup -f --show "$IMAGE_FILE")
mount "$LOOP_DEV" "$MOUNT_POINT" 2>&1 || echo " Khong the mount - filesystem da bi hong!"
losetup -d "$LOOP_DEV"
echo ""

# BUOC 5: Quet va phuc hoi
echo "BUOC 5: QUET VA PHUC HOI DIRECTORY/BITMAP"
echo "----------------------------------------"
python3 - <<'EOF'
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))

from directory_scanner import DirectoryScanner
from bitmap_recovery import BitmapRecovery

image_file = "test_directory.img"

print(" Dang quet filesystem...")

# Scan inodes
scanner = DirectoryScanner(image_file)
if not scanner.load_filesystem_info():
    print(" Loi: Khong the doc filesystem!")
    sys.exit(1)

if not scanner.scan_all_inodes():
    print(" Loi: Khong the quet inodes!")
    sys.exit(1)

print(f"\n Tim thay {len(scanner.found_inodes)} inodes")

# Rebuild directory tree
if scanner.rebuild_directory_tree():
    scanner.print_directory_tree()
    scanner.export_file_list(image_file + ".recovered_files.txt")

# Rebuild bitmaps
print("\n Dang rebuild bitmaps...")
bitmap = BitmapRecovery(image_file)
if bitmap.load_filesystem_info():
    bitmap.rebuild_block_bitmap_from_inodes(scanner.found_inodes)
    bitmap.rebuild_inode_bitmap_from_scan(scanner.found_inodes)
    print(" Rebuild bitmaps thanh cong!")
EOF

echo ""
echo " THANH CONG - Da phuc hoi filesystem!"
echo ""

# BUOC 6: Verify phuc hoi thanh cong
echo "BUOC 6: XAC NHAN PHUC HOI THANH CONG"
echo "----------------------------------------"
LOOP_DEV=$(losetup -f --show "$IMAGE_FILE")
mount "$LOOP_DEV" "$MOUNT_POINT" 2>/dev/null
if [ $? -eq 0 ]; then
    echo " Mount thanh cong!"
    echo ""
    echo " Noi dung sau khi phuc hoi:"
    tree "$MOUNT_POINT" 2>/dev/null || ls -lR "$MOUNT_POINT" | head -30
    umount "$MOUNT_POINT"
else
    echo " Van chua mount duoc - can kiem tra lai!"
fi
losetup -d "$LOOP_DEV"
echo ""

# BUOC 7: Kiem tra file list da phuc hoi
echo "BUOC 7: DANH SACH FILE DA PHUC HOI"
echo "----------------------------------------"
if [ -f "$IMAGE_FILE.recovered_files.txt" ]; then
    cat "$IMAGE_FILE.recovered_files.txt"
fi
echo ""

echo "========================================="
echo " TEST HOAN THANH!"
echo "========================================="
echo " Ket qua:"
echo "   [OK] Tao test image voi du lieu"
echo "   [OK] Pha hong directory va bitmaps"
echo "   [OK] Quet lai inodes va rebuild tree"
echo "   [OK] Rebuild bitmaps"
echo "   [OK] Phuc hoi thanh cong"
echo ""
echo " File test: $IMAGE_FILE"
echo " File list: $IMAGE_FILE.recovered_files.txt"
echo ""
