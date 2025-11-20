#!/bin/bash
set -e

# --- ĐỊNH NGHĨA MÀU SẮC ---
C_RESET='\033[0m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[0;33m'
C_BLUE='\033[0;34m'
C_CYAN='\033[0;36m'

# --- CÁC BIẾN CẤU HÌNH ---
IMAGE_FILE="test_directory.img"
IMAGE_SIZE_MB=50
MOUNT_POINT="/mnt/test_directory"
RECOVERY_SCRIPT="main.py"

# --- KIỂM TRA QUYỀN ROOT ---
if [ "$(id -u)" -ne 0 ]; then
  echo -e "${C_RED}Loi: Vui long chay voi quyen root.${C_RESET}"
  exit 1
fi

if [ ! -f "$RECOVERY_SCRIPT" ]; then
    echo -e "${C_RED}Loi: Khong tim thay '$RECOVERY_SCRIPT'.${C_RESET}"
    exit 1
fi

echo -e "${C_CYAN}========================================================================${C_RESET}"
echo -e "${C_CYAN}TAO IMAGE MAU CHO DIRECTORY & BITMAP RECOVERY${C_RESET}"
echo -e "${C_CYAN}========================================================================${C_RESET}"

# --- BƯỚC 0: DỌN DẸP ---
echo -e "\n${C_YELLOW}[0/6] Dang don dep moi truong cu...${C_RESET}"
umount "$MOUNT_POINT" 2>/dev/null || true
losetup -D 2>/dev/null || true
rm -f "$IMAGE_FILE"
mkdir -p "$MOUNT_POINT"
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 1: TẠO FILE IMAGE ---
echo -e "\n${C_YELLOW}[1/6] Tao file image ${IMAGE_SIZE_MB}MB...${C_RESET}"
echo -e "${C_BLUE}\$ dd if=/dev/zero of=$IMAGE_FILE bs=1M count=$IMAGE_SIZE_MB status=none${C_RESET}"
dd if=/dev/zero of="$IMAGE_FILE" bs=1M count=$IMAGE_SIZE_MB status=none
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 2: FORMAT EXT4 ---
echo -e "\n${C_YELLOW}[2/6] Format thanh EXT4 filesystem...${C_RESET}"
echo -e "${C_BLUE}\$ mkfs.ext4 -F $IMAGE_FILE > /dev/null 2>&1${C_RESET}"
mkfs.ext4 -F "$IMAGE_FILE" > /dev/null 2>&1
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 3: MOUNT IMAGE ---
echo -e "\n${C_YELLOW}[3/6] Mount image...${C_RESET}"
LOOP_DEVICE=$(losetup -f --show "$IMAGE_FILE")
echo -e "${C_BLUE}Loop device: $LOOP_DEVICE${C_RESET}"
echo -e "${C_BLUE}\$ mount $LOOP_DEVICE $MOUNT_POINT${C_RESET}"
mount "$LOOP_DEVICE" "$MOUNT_POINT"
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 4: TẠO CẤU TRÚC THƯ MUC ---
echo -e "\n${C_YELLOW}[4/6] Tao cau truc thu muc va du lieu test...${C_RESET}"

# Tạo thư mục
echo -e "${C_BLUE}\$ mkdir -p $MOUNT_POINT/{backup,data/{subdir1,subdir2},docs,images}${C_RESET}"
mkdir -p "$MOUNT_POINT"/{backup,data/{subdir1,subdir2},docs,images}

# Tạo files với nội dung
echo -e "${C_BLUE}\$ Tao cac file test...${C_RESET}"
echo "This is a test file - HCMUS Data Recovery Project" > "$MOUNT_POINT/test.txt"
echo "# README - EXT4 Directory Recovery Test" > "$MOUNT_POINT/README.md"

# /backup
echo "-- MySQL Backup File --" > "$MOUNT_POINT/backup/backup.sql"
echo "INSERT INTO users VALUES (1, 'admin', 'password');" >> "$MOUNT_POINT/backup/backup.sql"

# /data/subdir1
echo "File 1 content in subdirectory 1" > "$MOUNT_POINT/data/subdir1/file1.txt"

# /data/subdir2
echo "File 2 content in subdirectory 2" > "$MOUNT_POINT/data/subdir2/file2.txt"

# /docs
echo "[Config]" > "$MOUNT_POINT/docs/config.ini"
echo "server=localhost" >> "$MOUNT_POINT/docs/config.ini"
echo "port=3306" >> "$MOUNT_POINT/docs/config.ini"

echo "IMPORTANT: This is critical data!" > "$MOUNT_POINT/docs/important.txt"

echo "# Project Documentation" > "$MOUNT_POINT/docs/readme.txt"
echo "Version: 1.0" >> "$MOUNT_POINT/docs/readme.txt"

# /images (fake image files)
echo "FAKE_JPG_DATA_HEADER" > "$MOUNT_POINT/images/photo.jpg"
dd if=/dev/urandom of="$MOUNT_POINT/images/photo.jpg" bs=1K count=10 2>/dev/null

echo "FAKE_PNG_DATA_HEADER" > "$MOUNT_POINT/images/picture.png"
dd if=/dev/urandom of="$MOUNT_POINT/images/picture.png" bs=1K count=5 2>/dev/null

echo -e "${C_GREEN}Done - Da tao 10 files trong 5 thu muc${C_RESET}"

# --- BƯỚC 5: LIỆT KÊ CẤU TRÚC ---
echo -e "\n${C_YELLOW}[5/6] Cau truc thu muc:${C_RESET}"
echo -e "${C_BLUE}\$ find $MOUNT_POINT -type f | grep -v lost+found${C_RESET}"
find "$MOUNT_POINT" -type f | grep -v lost+found | sort

# Đếm files và directories
FILE_COUNT=$(find "$MOUNT_POINT" -type f | grep -v lost+found | wc -l)
DIR_COUNT=$(find "$MOUNT_POINT" -type d | grep -v lost+found | wc -l)
echo -e "\n${C_GREEN}Tong ket: $FILE_COUNT files, $DIR_COUNT directories${C_RESET}"

# --- BƯỚC 6: UNMOUNT VÀ CLEANUP ---
echo -e "\n${C_YELLOW}[6/6] Unmount va cleanup...${C_RESET}"
echo -e "${C_BLUE}\$ umount $MOUNT_POINT${C_RESET}"
umount "$MOUNT_POINT"
echo -e "${C_BLUE}\$ losetup -d $LOOP_DEVICE${C_RESET}"
losetup -d "$LOOP_DEVICE"
echo -e "${C_GREEN}Done${C_RESET}"

# --- KẾT QUẢ ---
echo -e "\n${C_CYAN}========================================================================${C_RESET}"
echo -e "${C_GREEN}HOAN TAT TAO IMAGE MAU!${C_RESET}"
echo -e "${C_CYAN}========================================================================${C_RESET}"
echo -e "\n${C_YELLOW}File:${C_RESET} $IMAGE_FILE (${IMAGE_SIZE_MB}MB)"
echo -e "${C_YELLOW}Du lieu:${C_RESET} $FILE_COUNT files trong $DIR_COUNT directories"
echo -e "\n${C_CYAN}Su dung main.py de:${C_RESET}"
echo -e "  ${C_GREEN}1.${C_RESET} Kiem tra du lieu (option 1)"
echo -e "  ${C_GREEN}2.${C_RESET} Pha hong directory/bitmap (option 2)"
echo -e "  ${C_GREEN}3.${C_RESET} Phuc hoi du lieu (option 3)"
echo -e "\n${C_BLUE}Chay:${C_RESET} sudo python3 main.py $IMAGE_FILE"
echo -e "${C_CYAN}========================================================================${C_RESET}"
