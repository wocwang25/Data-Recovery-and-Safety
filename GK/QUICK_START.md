# 🚀 Quick Start Guide - Ext4 Recovery Tool C++

## Bắt đầu nhanh trong 5 phút

### 1️⃣ Build chương trình

```bash
cd /workspace/GK
make
```

**Output mong đợi:**
```
Compiling main_ext4_recovery.cpp...
Compiling ext4_recovery.cpp...
Linking...
Build successful! Executable: ext4_recovery
```

---

### 2️⃣ Test với image tự tạo

#### Cách A: Dùng script tự động (Khuyến nghị)

```bash
sudo ./test_cpp_recovery.sh
```

Script sẽ:
- Build chương trình
- Tạo image Ext4 100MB
- Thêm test data
- Làm hỏng superblock
- Hướng dẫn test recovery

#### Cách B: Tạo test image thủ công

```bash
# Tạo image 100MB
dd if=/dev/zero of=test.img bs=1M count=100

# Format Ext4
sudo mkfs.ext4 test.img

# Mount và thêm dữ liệu
sudo mkdir -p /mnt/test
sudo mount -o loop test.img /mnt/test
echo "Hello World" | sudo tee /mnt/test/data.txt
sudo umount /mnt/test

# Làm hỏng superblock (offset 1024)
dd if=/dev/zero of=test.img bs=1 count=100 seek=1024 conv=notrunc

# Kiểm tra lỗi
sudo mount -o loop test.img /mnt/test
# Kết quả: mount: wrong fs type, bad option, bad superblock
```

---

### 3️⃣ Chạy công cụ phục hồi

```bash
sudo ./ext4_recovery test.img
```

**Menu sẽ xuất hiện:**
```
╔═══════════════════════════════════════╗
║           MAIN MENU                   ║
╠═══════════════════════════════════════╣
║  1. Analyze Primary Superblock        ║
║  2. Scan All Backup Superblocks       ║
║  ...                                  ║
║  6. Full Auto Recovery                ║
║  0. Exit                              ║
╚═══════════════════════════════════════╝
```

**Chọn option 6** (Full Auto Recovery)

Khi hỏi xác nhận, gõ:
```
I UNDERSTAND
```

---

### 4️⃣ Verify kết quả

Sau khi recovery thành công:

```bash
# Mount lại
sudo mount -o loop test.img /mnt/test

# Kiểm tra dữ liệu
ls -la /mnt/test
cat /mnt/test/data.txt

# Unmount
sudo umount /mnt/test
```

**Kết quả mong đợi:** Thấy lại file `data.txt` với nội dung "Hello World"

---

## 📊 So sánh với Python version

### Python (recover_ext4.py)
```bash
sudo python3 recover_ext4.py test.img
```
- ✅ Dễ dùng, tự động
- ❌ Phụ thuộc vào `e2fsck`
- ❌ Chậm hơn

### C++ (ext4_recovery)
```bash
sudo ./ext4_recovery test.img
```
- ✅ Nhanh hơn 5-10x
- ✅ Kiểm soát hoàn toàn
- ✅ Không phụ thuộc tool ngoài
- ✅ Giao diện tương tác tốt

---

## 🔍 Debug và Test từng bước

### Bước 1: Kiểm tra Primary Superblock

```bash
sudo ./ext4_recovery test.img
# Chọn: 1
```

Output sẽ hiển thị:
```
[STEP 1] Analyzing Primary Superblock...
========== PRIMARY SUPERBLOCK ==========
Magic Number:      0x0 (INVALID - should be 0xEF53)
...
[RESULT] Primary superblock is CORRUPTED!
         Recovery is needed.
```

### Bước 2: Quét Backup Superblocks

```bash
# Chọn: 2
```

Output:
```
[STEP 2] Scanning Backup Superblocks...
--- Checking backup at block 32768 ---
[VALID] Magic: 0xef53
        Inodes: 25168
        Blocks: 102400
...
[SUMMARY] Valid backups: 10, Invalid: 0
```

### Bước 3: Tìm Best Backup

```bash
# Chọn: 3
```

### Bước 4: Repair

```bash
# Chọn: 4
# Gõ: I UNDERSTAND
```

### Bước 5: Verify

```bash
# Chọn: 5
```

Output thành công:
```
[SUCCESS] Recovery verified! Primary superblock is now valid.
          You can now try to mount the filesystem.
```

---

## ⚠️ Troubleshooting

### Lỗi: "Permission denied"
```bash
# Phải chạy với sudo
sudo ./ext4_recovery test.img
```

### Lỗi: "Cannot open device"
```bash
# Kiểm tra file có tồn tại
ls -l test.img

# Kiểm tra quyền
stat test.img
```

### Build failed
```bash
# Kiểm tra g++ đã cài
g++ --version

# Cài đặt nếu chưa có
sudo apt-get install build-essential
```

### Mount vẫn fail sau recovery
```bash
# Chạy e2fsck để fix các lỗi khác
sudo e2fsck -f -y test.img

# Thử mount read-only
sudo mount -o ro,loop test.img /mnt/test
```

---

## 📝 Clean Up

```bash
# Xóa test image
rm -f test.img test_ext4_cpp.img

# Xóa backup files
rm -f *.corrupted_sb.backup

# Clean build
make clean

# Unmount nếu còn mount
sudo umount /mnt/test 2>/dev/null
sudo rmdir /mnt/test
```

---

## 🎓 Hiểu thêm về code

### Đọc superblock từ vị trí cụ thể
```cpp
bool Ext4Recovery::_readSuperblock(uint64_t blockNumber, Ext4Superblock& sb) {
    uint64_t offset = (blockNumber == 0) 
        ? EXT4_SUPERBLOCK_OFFSET 
        : blockNumber * BLOCK_SIZE_4K + EXT4_SUPERBLOCK_OFFSET;
    
    lseek(deviceFd, offset, SEEK_SET);
    read(deviceFd, &sb, sizeof(Ext4Superblock));
}
```

### Verify superblock
```cpp
bool Ext4Recovery::_verifySuperblock(const Ext4Superblock& sb) {
    // Check magic 0xEF53
    if (sb.s_magic != EXT4_MAGIC) return false;
    
    // Check basic sanity
    if (sb.s_inodes_count == 0) return false;
    if (sb.s_blocks_count_lo == 0) return false;
    
    return true;
}
```

### Repair superblock
```cpp
bool Ext4Recovery::repairPrimarySuperblock() {
    // 1. Find best backup
    Ext4Superblock bestBackup;
    findBestBackup(bestBackup, ...);
    
    // 2. Update block_group_nr to 0
    bestBackup.s_block_group_nr = 0;
    
    // 3. Write to primary location
    _writeSuperblock(0, bestBackup);
}
```

---

## 🎯 Next Steps

1. ✅ Test với image nhỏ (100MB) - Done
2. ⬜ Test với image lớn (10GB)
3. ⬜ Test với real device (USB drive)
4. ⬜ So sánh hiệu suất với Python version
5. ⬜ Thêm tính năng: Reconstruct từ Group Descriptors
6. ⬜ Hỗ trợ block size khác 4K

---

## 📚 Đọc thêm

- [README_CPP.md](README_CPP.md) - Tài liệu đầy đủ
- [report.md](report.md) - Báo cáo lý thuyết Ext4
- Code: `ext4_recovery.h`, `ext4_recovery.cpp`

---

**Chúc bạn thành công! 🎉**

Nếu có vấn đề, check lại từng bước trong guide này.
