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
IMAGE_FILE="test_disk_multipart.img"
IMAGE_SIZE_MB=2000
PART1_SIZE_MB=500
PART2_SIZE_MB=800
PART1_START_MB=1
PART2_START_MB=510
MOUNT_POINT_1="/mnt/part1_test"
MOUNT_POINT_2="/mnt/part2_test"
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

echo -e "${C_CYAN}=== BAT DAU KICH BAN KIEM THU PARTITION ===${C_RESET}"

# --- BƯỚC 0: DỌN DẸP ---
echo -e "${C_YELLOW}[0/9] Dang don dep moi truong cu...${C_RESET}"
umount "$MOUNT_POINT_1" 2>/dev/null || true
umount "$MOUNT_POINT_2" 2>/dev/null || true
rm -f "$IMAGE_FILE"
mkdir -p "$MOUNT_POINT_1"
mkdir -p "$MOUNT_POINT_2"

# --- BƯỚC 1: TẠO FILE IMAGE ---
echo -e "\n${C_YELLOW}[1/9] Tao file image ${IMAGE_SIZE_MB}MB...${C_RESET}"
echo -e "${C_BLUE}\$ dd if=/dev/zero of=$IMAGE_FILE bs=1M count=$IMAGE_SIZE_MB status=none${C_RESET}"
dd if=/dev/zero of="$IMAGE_FILE" bs=1M count=$IMAGE_SIZE_MB status=none
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 2: TẠO PARTITION TABLE ---
echo -e "\n${C_YELLOW}[2/9] Tao partition table voi 2 partitions...${C_RESET}"
echo -e "${C_BLUE}\$ parted -s $IMAGE_FILE mklabel msdos${C_RESET}"
parted -s "$IMAGE_FILE" mklabel msdos

echo -e "${C_BLUE}\$ parted -s $IMAGE_FILE mkpart primary ext4 ${PART1_START_MB}MiB ${PART1_SIZE_MB}MiB${C_RESET}"
parted -s "$IMAGE_FILE" mkpart primary ext4 ${PART1_START_MB}MiB ${PART1_SIZE_MB}MiB

echo -e "${C_BLUE}\$ parted -s $IMAGE_FILE mkpart primary ext4 ${PART2_START_MB}MiB $((PART2_START_MB + PART2_SIZE_MB))MiB${C_RESET}"
parted -s "$IMAGE_FILE" mkpart primary ext4 ${PART2_START_MB}MiB $((PART2_START_MB + PART2_SIZE_MB))MiB

echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 3: SETUP LOOP DEVICE ---
echo -e "\n${C_YELLOW}[3/9] Setup loop device...${C_RESET}"
LOOP_DEVICE=$(losetup -f --show "$IMAGE_FILE")
echo -e "${C_BLUE}Loop device: $LOOP_DEVICE${C_RESET}"
partprobe "$LOOP_DEVICE"
sleep 2

# --- BƯỚC 4: FORMAT PARTITION 1 ---
echo -e "\n${C_YELLOW}[4/9] Format partition 1 (EXT4)...${C_RESET}"
echo -e "${C_BLUE}\$ mkfs.ext4 -F ${LOOP_DEVICE}p1 > /dev/null 2>&1${C_RESET}"
mkfs.ext4 -F "${LOOP_DEVICE}p1" > /dev/null 2>&1
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 5: FORMAT PARTITION 2 ---
echo -e "\n${C_YELLOW}[5/9] Format partition 2 (EXT4)...${C_RESET}"
echo -e "${C_BLUE}\$ mkfs.ext4 -F ${LOOP_DEVICE}p2 > /dev/null 2>&1${C_RESET}"
mkfs.ext4 -F "${LOOP_DEVICE}p2" > /dev/null 2>&1
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 6: THÊM DỮ LIỆU PARTITION 1 ---
echo -e "\n${C_YELLOW}[6/9] Them du lieu test vao partition 1...${C_RESET}"
echo -e "${C_BLUE}\$ mount ${LOOP_DEVICE}p1 $MOUNT_POINT_1${C_RESET}"
mount "${LOOP_DEVICE}p1" "$MOUNT_POINT_1"

echo -e "${C_BLUE}\$ echo \"Data on Partition 1 - HCMUS\" > $MOUNT_POINT_1/data1.txt${C_RESET}"
echo "Data on Partition 1 - HCMUS" > "$MOUNT_POINT_1/data1.txt"
mkdir -p "$MOUNT_POINT_1/folder1"
echo "Nested data in partition 1" > "$MOUNT_POINT_1/folder1/nested.txt"

echo -e "${C_BLUE}\$ ls -l $MOUNT_POINT_1${C_RESET}"
ls -l "$MOUNT_POINT_1"

echo -e "${C_BLUE}\$ umount $MOUNT_POINT_1${C_RESET}"
umount "$MOUNT_POINT_1"
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 7: THÊM DỮ LIỆU PARTITION 2 ---
echo -e "\n${C_YELLOW}[7/9] Them du lieu test vao partition 2...${C_RESET}"
echo -e "${C_BLUE}\$ mount ${LOOP_DEVICE}p2 $MOUNT_POINT_2${C_RESET}"
mount "${LOOP_DEVICE}p2" "$MOUNT_POINT_2"

echo -e "${C_BLUE}\$ echo \"Data on Partition 2 - HCMUS\" > $MOUNT_POINT_2/data2.txt${C_RESET}"
echo "Data on Partition 2 - HCMUS" > "$MOUNT_POINT_2/data2.txt"
mkdir -p "$MOUNT_POINT_2/folder2"
echo "Another nested data in partition 2" > "$MOUNT_POINT_2/folder2/nested2.txt"

echo -e "${C_BLUE}\$ ls -l $MOUNT_POINT_2${C_RESET}"
ls -l "$MOUNT_POINT_2"

echo -e "${C_BLUE}\$ umount $MOUNT_POINT_2${C_RESET}"
umount "$MOUNT_POINT_2"
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 8: DETACH LOOP DEVICE ---
echo -e "\n${C_YELLOW}[8/9] Detach loop device...${C_RESET}"
echo -e "${C_BLUE}\$ losetup -d $LOOP_DEVICE${C_RESET}"
losetup -d "$LOOP_DEVICE"
echo -e "${C_GREEN}Done${C_RESET}"

# --- BƯỚC 9: LÀM HỎNG PARTITION TABLE ---
echo -e "\n${C_RED}[9/9] LAM HONG PARTITION TABLE (512 bytes dau)...${C_RESET}"

echo -e "${C_BLUE}\$ dd if=/dev/zero of=$IMAGE_FILE bs=512 count=1 conv=notrunc status=none${C_RESET}"
dd if=/dev/zero of="$IMAGE_FILE" bs=512 count=1 conv=notrunc status=none
echo -e "${C_GREEN}Done - Da lam hong partition table!${C_RESET}"

# --- KẾT QUẢ ---
echo -e "\n${C_CYAN}============================================================${C_RESET}"
echo -e "${C_GREEN}HOAN TAT TAO TEST DISK!${C_RESET}"
echo -e "${C_CYAN}============================================================${C_RESET}"