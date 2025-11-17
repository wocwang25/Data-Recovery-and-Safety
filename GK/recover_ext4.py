#!/usr/bin/env python3
# 1. Thử tìm backup block tự động bằng 'mke2fs'.
# 2. Nếu thất bại (do superblock chính hỏng),
#    chuyển sang Kế hoạch B:
# 3. Thử lặp qua một danh sách các backup block tiêu chuẩn (cho 4k block size).
# 4. Dừng lại ngay khi một backup block sửa chữa thành công.

import sys
import os
import subprocess
import re

# --- CẤU HÌNH ---
# Danh sách backup block tiêu chuẩn (cho 4k block size)
# Đây là Kế hoạch B nếu 'mke2fs' thất bại.
STANDARD_BACKUP_BLOCKS = [32768, 98304, 163840, 229376, 294912]

def check_permissions_and_args():
    #Kiểm tra quyền root và tham số đầu vào
    if os.geteuid() != 0:
        print("Lỗi: Kịch bản này phải được chạy với quyền root (sudo).")
        return None

    if len(sys.argv) != 2:
        print(f"Lỗi: Cú pháp không đúng.")
        print(f"Cách dùng: (sudo) {sys.argv[0]} /path/to/device_or_image")
        return None

    target_device = sys.argv[1]
    if not os.path.exists(target_device):
        print(f"Lỗi: Thiết bị hoặc file '{target_device}' không tồn tại.")
        return None

    print(f"[INFO] Mục tiêu phục hồi: {target_device}")
    return target_device

def get_backup_blocks(target_device):
    print("\n[1/4] Đang thử tìm backup superblock tự động (Kế hoạch A)...")
    try:
        cmd_find = ['mke2fs', '-n', '-F', '-b', '4096', target_device]
        result = subprocess.run(cmd_find, capture_output=True, text=True, check=False)
        output_to_parse = result.stderr

        match = re.search(r'Superblock backups stored on blocks:\s*([\d,\s]+)', output_to_parse)

        if match:
            print("[INFO] Kế hoạch A thành công: Tìm thấy thông tin tự động.")
            block_string = match.group(1).strip()
            backup_blocks = [int(b.strip()) for b in block_string.split(',') if b.strip()]
            if backup_blocks:
                print(f"[INFO] Danh sách backup tìm được: {backup_blocks}")
                return backup_blocks

    except Exception as e:
        print(f"[LỖI KẾ HOẠCH A] Lỗi khi chạy mke2fs: {e}")

    # --- Nếu Kế hoạch A thất bại ---
    print("[INFO] Kế hoạch A thất bại (có thể do superblock chính đã hỏng).")
    print("[INFO] Chuyển sang Kế hoạch B: Sử dụng danh sách backup tiêu chuẩn.")
    print(f"[INFO] Danh sách sẽ thử: {STANDARD_BACKUP_BLOCKS}")
    return STANDARD_BACKUP_BLOCKS

def attempt_recovery(target_device, backup_blocks):
    print("\n[2/4] Bắt đầu quá trình sửa chữa...")

    for block in backup_blocks:
        print(f"\n--- Đang thử với backup block: {block} ---")

        cmd_recover = ['e2fsck', '-f', '-y', '-b', str(block), target_device]
        print(f"[INFO] Đang thực thi: {' '.join(cmd_recover)}")

        try:
            result = subprocess.run(cmd_recover, capture_output=True, text=True, check=False)

            # In ra kết quả để debug
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"[STDERR]:\n{result.stderr}")

            # Mã lỗi e2fsck: 0=OK, 1=Đã sửa, 2=Đã sửa+cần reboot
            if result.returncode <= 2:
                print(f"\n[THÀNH CÔNG] Sửa chữa thành công sử dụng block {block} (mã lỗi: {result.returncode}).")
                print("Superblock chính đã được phục hồi.")
                return True # Báo hiệu thành công
            else:
                print(f"[THẤT BẠI] Block {block} không thành công (mã lỗi: {result.returncode}). Đang thử block tiếp theo...")

        except Exception as e:
            print(f"[LỖI] Lỗi bất ngờ khi chạy e2fsck với block {block}: {e}")

    # Nếu chạy hết vòng lặp mà không thành công
    print("\n[LỖI NGHIÊM TRỌNG] Đã thử tất cả backup block nhưng đều thất bại.")
    return False # Báo hiệu thất bại

def verify_filesystem(target_device):
    """
    Chạy e2fsck lần cuối (không cần -b) để xác minh superblock chính đã ổn.
    """
    print("\n[3/4] Đang chạy kiểm tra lần cuối để xác minh (sử dụng superblock chính)...")
    cmd_verify = ['e2fsck', '-f', '-y', target_device]
    print(f"[INFO] Đang thực thi: {' '.join(cmd_verify)}")

    try:
        result_verify = subprocess.run(cmd_verify, capture_output=True, text=True, check=False)
        print("\n--- Kết quả xác minh ---")
        print(result_verify.stdout)
        if result_verify.stderr:
            print(f"[STDERR]:\n{result_verify.stderr}")

        if result_verify.returncode <= 2:
            print(f"[THÀNH CÔNG] Xác minh hoàn tất (mã lỗi: {result_verify.returncode}). Hệ thống file đã ổn định.")
            return True
        else:
            print(f"[LỖI] e2fsck (xác minh) thất bại với mã lỗi {result_verify.returncode}.")
            return False
    except Exception as e:
        print(f"[LỖI] Lỗi bất ngờ khi xác minh: {e}")
        return False

def main():
    """Hàm thực thi chính."""
    print("--- Trình Phục Hồi Superblock EXT4 ---")

    target_device = check_permissions_and_args()
    if not target_device:
        sys.exit(1)

    backup_blocks_to_try = get_backup_blocks(target_device)
    if not backup_blocks_to_try:
        print("Lỗi: Không tìm thấy danh sách backup block để thử.")
        sys.exit(1)

    recovery_successful = attempt_recovery(target_device, backup_blocks_to_try)
    if not recovery_successful:
        print("Quá trình phục hồi thất bại.")
        sys.exit(1)

    verification_successful = verify_filesystem(target_device)
    if not verification_successful:
        print("Quá trình xác minh thất bại. Dữ liệu có thể chưa an toàn.")
        sys.exit(1)

    # --- KẾT THÚC ---
    print("\n[4/4] === QUÁ TRỊNH PHỤC HỒI HOÀN TẤT VÀ ĐÃ XÁC MINH ===")
    print("Bạn có thể thử mount file image (chỉ đọc) để kiểm tra dữ liệu:")
    print("1. Tạo thư mục: mkdir -p /mnt/recovery_test")
    print(f"2. Mount (chỉ đọc): mount -o ro,loop {target_device} /mnt/recovery_test")
    print("3. Kiểm tra: ls -lha /mnt/recovery_test")
    print("4. Unmount: umount /mnt/recovery_test")

if __name__ == "__main__":
    main()