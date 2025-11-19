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