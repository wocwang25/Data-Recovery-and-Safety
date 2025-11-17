#!/bin/bash
# Dừng ngay nếu có bất kỳ lệnh nào thất bại
set -e

# --- ĐỊNH NGHĨA MÀU SẮC ---
C_RESET='\033[0m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[0;33m'
C_BLUE='\033[0;34m'       # Sẽ dùng màu này để in lệnh
C_CYAN='\033[0;36m'

# --- CÁC BIẾN CẤU HÌNH ---
IMAGE_FILE="test_image_1gb.img"
MOUNT_POINT="/mnt/recovery_test"
TEST_FILE_NAME="test_data.txt"
RECOVERY_SCRIPT="recover_ext4.py"

# --- BƯỚC 0: KIỂM TRA QUYỀN ROOT VÀ SCRIPT ---
if [ "$(id -u)" -ne 0 ]; then
  echo -e "${C_RED}Lỗi: Vui lòng chạy kịch bản này với quyền root.${C_RESET}"
  exit 1
fi

if [ ! -f "$RECOVERY_SCRIPT" ]; then
    echo -e "${C_RED}Lỗi: Không tìm thấy file script Python '$RECOVERY_SCRIPT'.${C_RESET}"
    echo "Hãy chắc chắn nó ở cùng thư mục."
    exit 1
fi

echo -e "${C_CYAN}=== BẮT ĐẦU KỊCH BẢN KIỂM THỬ TỰ ĐỘNG ===${C_RESET}"

# --- Dọn dẹp môi trường cũ (nếu có) ---
echo -e "${C_YELLOW}[0/6] Đang dọn dẹp môi trường cũ (nếu có)...${C_RESET}"
echo -e "${C_BLUE}\$ umount $MOUNT_POINT || true${C_RESET}"
umount "$MOUNT_POINT" || true
echo -e "${C_BLUE}\$ rm -f $IMAGE_FILE${C_RESET}"
rm -f "$IMAGE_FILE"
echo -e "${C_BLUE}\$ mkdir -p $MOUNT_POINT${C_RESET}"
mkdir -p "$MOUNT_POINT"

# --- BƯỚC 1: TẠO FILE ẢNH VÀ FORMAT ---
echo -e "\n${C_YELLOW}[1/6] Đang tạo file ảnh 1GB và format ext4...${C_RESET}"
echo -e "${C_BLUE}\$ dd if=/dev/zero of=$IMAGE_FILE bs=1M count=1024 status=none${C_RESET}"
dd if=/dev/zero of="$IMAGE_FILE" bs=1M count=1024 status=none

echo -e "${C_BLUE}\$ mke2fs -t ext4 -F $IMAGE_FILE > /dev/null 2>&1${C_RESET}"
mke2fs -t ext4 -F "$IMAGE_FILE" > /dev/null 2>&1

# --- BƯỚC 2: THÊM DỮ LIỆU KIỂM THỬ ---
echo -e "\n${C_YELLOW}[2/6] Đang thêm dữ liệu kiểm thử ('$TEST_FILE_NAME')...${C_RESET}"
echo -e "${C_BLUE}\$ mount -o loop $IMAGE_FILE $MOUNT_POINT${C_RESET}"
mount -o loop "$IMAGE_FILE" "$MOUNT_POINT"

echo -e "${C_BLUE}\$ echo \"DU LIEU NAY PHAI DUOC PHUC HOI\" > $MOUNT_POINT/$TEST_FILE_NAME${C_RESET}"
echo "DU LIEU NAY PHAI DUOC PHUC HOI" > "$MOUNT_POINT/$TEST_FILE_NAME"

echo -e "${C_BLUE}\$ ls -l $MOUNT_POINT${C_RESET}"
ls -l "$MOUNT_POINT"

echo -e "${C_BLUE}\$ umount $MOUNT_POINT${C_RESET}"
umount "$MOUNT_POINT"

# --- BƯỚC 3: LÀM HỎNG SUPERBLOCK CHÍNH ---
echo -e "\n${C_RED}[3/6] Đang LÀM HỎNG Superblock chính (offset 1024)...${C_RESET}"
echo -e "${C_BLUE}\$ dd if=/dev/zero of=$IMAGE_FILE bs=1 count=100 seek=1024 conv=notrunc status=none${C_RESET}"
dd if=/dev/zero of="$IMAGE_FILE" bs=1 count=100 seek=1024 conv=notrunc status=none

# --- BƯỚC 4: CHẠY SCRIPT PHỤC HỒI ---
echo -e "\n${C_CYAN}[4/6] Đang chạy script phục hồi '$RECOVERY_SCRIPT'...${C_RESET}"
echo -e "${C_BLUE}\$ python3 $RECOVERY_SCRIPT $IMAGE_FILE${C_RESET}"
# Cho script Python chạy và hiển thị output của nó
python3 "$RECOVERY_SCRIPT" "$IMAGE_FILE"

# --- BƯỚC 5: KIỂM TRA KẾT QUẢ ---
echo -e "\n${C_GREEN}[5/6] Đang xác minh kết quả phục hồi...${C_RESET}"
echo -e "${C_BLUE}\$ mount -o loop $IMAGE_FILE $MOUNT_POINT${C_RESET}"
mount -o loop "$IMAGE_FILE" "$MOUNT_POINT"

echo "Kiểm tra sự tồn tại của file '$TEST_FILE_NAME'..."

if [ -f "$MOUNT_POINT/$TEST_FILE_NAME" ]; then
    echo -e "${C_GREEN}✅✅✅ THÀNH CÔNG! ✅✅✅${C_RESET}"
    echo -e "${C_GREEN}File '$TEST_FILE_NAME' đã được tìm thấy!${C_RESET}"
    echo "Nội dung file:"
    echo -e "${C_BLUE}\$ cat $MOUNT_POINT/$TEST_FILE_NAME${C_RESET}"
    cat "$MOUNT_POINT/$TEST_FILE_NAME"
else
    echo -e "${C_RED}❌❌❌ THẤT BẠI! ❌❌❌${C_RESET}"
    echo -e "${C_RED}File '$TEST_FILE_NAME' không tìm thấy sau khi phục hồi!${C_RESET}"
fi

# --- BƯỚC 6: DỌN DẸP ---
echo -e "\n${C_YELLOW}[6/6] Đang dọn dẹp...${C_RESET}"
echo -e "${C_BLUE}\$ umount $MOUNT_POINT${C_RESET}"
umount "$MOUNT_POINT"
echo -e "${C_CYAN}=== HOÀN TẤT KIỂM THỬ ===${C_RESET}"
echo "File ảnh '$IMAGE_FILE' vẫn được giữ lại để bạn kiểm tra thủ công."