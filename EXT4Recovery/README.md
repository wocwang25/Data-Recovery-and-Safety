# EXT4 Data Recovery Tool

🛠️ **Công cụ phục hồi dữ liệu EXT4 Filesystem bằng Python**

Dự án này được phát triển dựa trên kiến trúc của FileSystem project (C++), áp dụng cho việc phục hồi dữ liệu từ EXT4 filesystem khi có tham số volume bị sai hoặc metadata bị hỏng.

## 📋 Mục lục

- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Kiến trúc](#kiến-trúc)
- [Cài đặt](#cài-đặt)
- [Sử dụng](#sử-dụng)
- [Các trường hợp phục hồi](#các-trường-hợp-phục-hồi)
- [Tài liệu tham khảo](#tài-liệu-tham-khảo)

## 🎯 Giới thiệu

EXT4 Data Recovery Tool là một công cụ dòng lệnh giúp phân tích và phục hồi dữ liệu từ các EXT4 filesystem bị hỏng. Công cụ đặc biệt hữu ích trong các tình huống:

- **Superblock bị hỏng**: Tìm và sử dụng backup superblocks
- **Group descriptor table lỗi**: Quét tìm metadata từ các vị trí dự phòng
- **Metadata bị mất**: Quét trực tiếp các inodes và data blocks
- **Phân tích filesystem**: Hiển thị cấu trúc và thông tin chi tiết

## ✨ Tính năng

### 1. Phân tích Superblock
- ✅ Đọc và hiển thị thông tin superblock chính
- ✅ Tìm kiếm backup superblocks tự động
- ✅ Phát hiện và báo cáo các tham số bị sai
- ✅ Hỗ trợ cả 32-bit và 64-bit mode

### 2. Quản lý Metadata
- ✅ Đọc group descriptor table
- ✅ Phân tích inode structures
- ✅ Liệt kê nội dung directories
- ✅ Quét tìm inodes khi metadata bị hỏng

### 3. Phục hồi Dữ liệu
- ✅ Phục hồi file từ inode number
- ✅ Hỗ trợ block pointers truyền thống
- ✅ Tạo báo cáo phục hồi chi tiết
- ⚠️ Extent tree support (đang phát triển)

### 4. Công cụ Phân tích
- ✅ Hex dump dữ liệu blocks
- ✅ Hiển thị thông tin chi tiết về inodes
- ✅ Tính toán và kiểm tra checksums
- ✅ Format dữ liệu dễ đọc

## 🏗️ Kiến trúc

Dự án được thiết kế theo mô hình module hóa, tương tự FileSystem project:

```
EXT4Recovery/
│
├── ext4_structures.py      # Định nghĩa các cấu trúc dữ liệu EXT4
│   ├── Superblock
│   ├── GroupDescriptor
│   ├── Inode
│   ├── DirectoryEntry
│   ├── ExtentHeader
│   └── Extent
│
├── ext4_utils.py           # Các hàm tiện ích
│   ├── EXT4Utils class
│   ├── read_block() / write_block()
│   ├── parse_superblock()
│   ├── parse_inode()
│   └── format_bytes()
│
├── ext4_recovery.py        # Logic phục hồi chính
│   ├── EXT4Recovery class
│   ├── open_device()
│   ├── find_backup_superblocks()
│   ├── read_group_descriptors()
│   ├── list_directory()
│   ├── recover_file()
│   └── scan_for_inodes()
│
├── main.py                 # Giao diện người dùng
│   └── Menu-driven interface
│
├── requirements.txt        # Dependencies
└── README.md              # Tài liệu này
```

### So sánh với FileSystem Project

| FileSystem (C++) | EXT4Recovery (Python) | Mục đích |
|-----------------|----------------------|----------|
| `header.h` | `ext4_structures.py` | Định nghĩa structures |
| `utils.cpp` | `ext4_utils.py` | Hàm tiện ích |
| `volume.cpp` | `ext4_recovery.py` | Logic chính |
| `main.cpp` | `main.py` | Giao diện |
| `md5.cpp` | `hashlib` (built-in) | Checksum |

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.7 trở lên
- Quyền đọc device/image file

### Cài đặt

1. **Clone repository**:
```bash
git clone <repository-url>
cd Data-Recovery-and-Safety/EXT4Recovery
```

2. **Cài đặt dependencies** (nếu có):
```bash
pip install -r requirements.txt
```

3. **Kiểm tra cài đặt**:
```bash
python main.py
```

### Chạy trên Linux
Để đọc device thật (ví dụ: `/dev/sdb1`), cần quyền root:
```bash
sudo python main.py
```

### Chạy trên Windows
Với Windows, có thể đọc disk image files trực tiếp:
```bash
python main.py
```

## 📖 Sử dụng

### 1. Khởi động chương trình

```bash
python main.py
```

### 2. Menu chính

Sau khi khởi động, bạn sẽ thấy menu:

```
📋 MENU CHÍNH
--------------------------------------------------------------
1. Mở device/image file
2. Hiển thị thông tin superblock
3. Tìm và hiển thị backup superblocks
4. Đọc group descriptors
5. Liệt kê thư mục root
6. Đọc inode cụ thể
7. Phục hồi file từ inode
8. Quét tìm inodes (khi metadata bị hỏng)
9. Tạo báo cáo phục hồi
0. Thoát
```

### 3. Workflow cơ bản

#### Bước 1: Mở device/image
```
Chọn: 1
Nhập đường dẫn: /path/to/disk.img
```

#### Bước 2: Xem thông tin
```
Chọn: 2  # Hiển thị superblock info
```

#### Bước 3: Nếu superblock bị hỏng
```
Chọn: 3  # Tìm backup superblocks
```

#### Bước 4: Đọc metadata
```
Chọn: 4  # Đọc group descriptors
```

#### Bước 5: Khám phá filesystem
```
Chọn: 5  # Liệt kê thư mục root
Chọn: 6  # Đọc inode cụ thể
```

#### Bước 6: Phục hồi dữ liệu
```
Chọn: 7  # Phục hồi file
Nhập inode: 12
Nhập output: recovered_file.txt
```

### 4. Ví dụ thực tế

#### Ví dụ 1: Phục hồi khi superblock bị hỏng

```python
# Tự động tìm backup và sử dụng
$ python main.py
[1] Mở device: disk.img
⚠️  Superblock chính bị hỏng, đang tìm backup...
✅ Tìm thấy backup tại group 1
✅ Tìm thấy backup tại group 3
✅ Tìm thấy backup tại group 5
```

#### Ví dụ 2: Quét tìm file khi metadata bị mất

```python
# Sử dụng chức năng quét
[8] Quét tìm inodes
Block bắt đầu: 0
Số blocks: 1000
✅ Tìm thấy 234 inodes
```

#### Ví dụ 3: Tạo báo cáo phục hồi

```python
[9] Tạo báo cáo phục hồi
✅ Đã lưu báo cáo vào recovery_report.txt
```

## 🔧 Các trường hợp phục hồi

### 1. Superblock bị hỏng

**Triệu chứng**:
- Không mount được filesystem
- Magic number không đúng (không phải 0xEF53)
- Các thông số không hợp lệ

**Giải pháp**:
```python
recovery = EXT4Recovery()
recovery.open_device("disk.img")  # Tự động tìm backup
recovery.print_superblock_info()
```

**Vị trí backup superblocks**:
- Group 0: Block 0 (superblock chính)
- Group 1, 3, 5, 7, 9: Backup superblocks
- Group 3^n, 5^n, 7^n: Backup superblocks bổ sung

### 2. Group Descriptor bị lỗi

**Triệu chứng**:
- Không tìm thấy inodes
- Inode table không đọc được
- Block/inode bitmaps sai

**Giải pháp**:
```python
# Đọc từ backup group descriptors
recovery.read_group_descriptors()

# Hoặc quét trực tiếp
inodes = recovery.scan_for_inodes(start_block=0, num_blocks=1000)
```

### 3. Inode bị mất/hỏng

**Triệu chứng**:
- File/directory không truy cập được
- Links count = 0
- Data pointers bị null

**Giải pháp**:
```python
# Quét toàn bộ partition
for block in range(0, total_blocks, 100):
    inodes = recovery.scan_for_inodes(block, 100)
    # Phân tích và phục hồi từng inode
```

### 4. Directory Entry bị lỗi

**Triệu chứng**:
- Không liệt kê được files
- Tên file bị lỗi
- Inode numbers không hợp lệ

**Giải pháp**:
```python
# Đọc trực tiếp từ inode của directory
inode = recovery.read_inode(2)  # Root directory
entries = recovery.list_directory(2)
```

## 📚 Kiến thức EXT4

### Cấu trúc EXT4 Filesystem

```
┌─────────────────────────────────────────────────────────┐
│ Boot Block (1024 bytes)                                 │
├─────────────────────────────────────────────────────────┤
│ Block Group 0                                           │
│  ├─ Superblock (1024 bytes)                            │
│  ├─ Group Descriptors                                  │
│  ├─ Reserved GDT Blocks                                │
│  ├─ Data Block Bitmap                                  │
│  ├─ Inode Bitmap                                       │
│  ├─ Inode Table                                        │
│  └─ Data Blocks                                        │
├─────────────────────────────────────────────────────────┤
│ Block Group 1                                           │
│  ├─ Superblock Backup (optional)                       │
│  ├─ ...                                                │
│  └─ ...                                                │
├─────────────────────────────────────────────────────────┤
│ ...                                                     │
└─────────────────────────────────────────────────────────┘
```

### Các thông số quan trọng

| Tham số | Mô tả | Vị trí trong Superblock |
|---------|-------|------------------------|
| Magic Number | 0xEF53 | Offset 56 (2 bytes) |
| Block Size | 1024, 2048, 4096 bytes | Offset 24 (4 bytes) |
| Inodes Count | Tổng số inodes | Offset 0 (4 bytes) |
| Blocks Count | Tổng số blocks | Offset 4 (4 bytes) |
| Inode Size | Thường 256 bytes | Offset 88 (2 bytes) |

### Feature Flags

```python
EXT4_FEATURE_INCOMPAT_EXTENTS = 0x0040  # Sử dụng extent tree
EXT4_FEATURE_INCOMPAT_64BIT = 0x0080    # Hỗ trợ 64-bit
EXT4_FEATURE_INCOMPAT_FLEX_BG = 0x0200  # Flexible block groups
```

## 🧪 Testing

### Tạo test image

```bash
# Tạo file image 100MB
dd if=/dev/zero of=test.img bs=1M count=100

# Format thành EXT4
mkfs.ext4 test.img

# Mount và thêm dữ liệu test
sudo mount -o loop test.img /mnt
sudo cp test_files/* /mnt/
sudo umount /mnt

# Làm hỏng superblock (để test recovery)
dd if=/dev/zero of=test.img bs=1024 count=1 seek=1 conv=notrunc
```

### Test recovery

```bash
python main.py
# Mở test.img
# Thử các chức năng phục hồi
```

## ⚠️ Lưu ý quan trọng

### An toàn dữ liệu
- ⚠️ **LUÔN** làm việc trên bản copy, không phải disk gốc
- ⚠️ Đảm bảo có backup trước khi thử nghiệm
- ⚠️ Không ghi dữ liệu lên disk đang phục hồi

### Quyền truy cập
- Linux: Cần `sudo` để đọc device files
- Windows: Chạy as Administrator nếu cần
- Kiểm tra permissions trước khi chạy

### Hạn chế hiện tại
- ⚠️ Extent tree chưa được implement đầy đủ
- ⚠️ Indirect blocks chưa hỗ trợ
- ⚠️ Journal replay chưa có
- ⚠️ Encrypted files không hỗ trợ

## 🔍 Troubleshooting

### Lỗi: "Permission denied"
```bash
# Giải pháp: Chạy với sudo
sudo python main.py
```

### Lỗi: "Magic number không hợp lệ"
```bash
# Giải pháp: Thử tìm backup superblock
# Menu → Option 3
```

### Lỗi: "Không đọc được inode"
```bash
# Giải pháp: Quét tìm inodes
# Menu → Option 8
```

### Lỗi: "File sử dụng extents"
```bash
# Hiện tại chưa hỗ trợ đầy đủ
# Cần implement extent tree parser
```

## 📊 Roadmap

### Version 1.0 (Hiện tại)
- ✅ Basic superblock recovery
- ✅ Backup superblock scanning
- ✅ Group descriptor reading
- ✅ Inode parsing
- ✅ Simple file recovery

### Version 2.0 (Kế hoạch)
- ⏳ Full extent tree support
- ⏳ Indirect blocks support
- ⏳ Journal analysis
- ⏳ Deleted file recovery
- ⏳ GUI interface

### Version 3.0 (Tương lai)
- ⏳ Network recovery
- ⏳ Automated recovery
- ⏳ Machine learning for pattern detection
- ⏳ Multiple filesystem support

## 🤝 Đóng góp

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Dự án này được phân phối theo giấy phép được quy định trong file LICENSE.

## 🙏 Tài liệu tham khảo

### Official Documentation
- [EXT4 Wiki](https://ext4.wiki.kernel.org/)
- [Linux Kernel Documentation](https://www.kernel.org/doc/html/latest/filesystems/ext4/)

### Books & Papers
- "Understanding the Linux Kernel" - Daniel P. Bovet
- "Ext4 Disk Layout" - Theodore Ts'o
- "File System Forensic Analysis" - Brian Carrier

### Tools
- `debugfs` - EXT4 debugging tool
- `e2fsck` - EXT4 filesystem checker
- `dumpe2fs` - EXT4 filesystem information

### Related Projects
- FileSystem Project (C++) - Base architecture
- TestDisk - Data recovery tool
- PhotoRec - File recovery tool

## 👥 Tác giả

- **Your Name** - Initial work

## 📞 Liên hệ

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

⭐ Nếu project này hữu ích, hãy cho một star!

**Cảnh báo**: Công cụ này chỉ nên được sử dụng cho mục đích học tập và nghiên cứu. Luôn backup dữ liệu quan trọng!
