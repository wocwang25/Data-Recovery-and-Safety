# Cấu trúc Module - EXT4 Directory Recovery

## 📁 Cấu trúc thư mục

```
EXT4_Directory/
├── main.py                  # Entry point chính (2.6 KB)
├── handlers.py              # Các handler xử lý menu (15.9 KB)
├── utils.py                 # Hàm tiện ích (2.4 KB)
├── ui.py                    # Giao diện menu (1.4 KB)
├── bitmap_recovery.py       # Core recovery logic (16.2 KB)
├── directory_scanner.py     # Scan và rebuild directory tree (11.6 KB)
├── test_auto.sh             # Script tạo test image
└── README.md                # Hướng dẫn sử dụng
```

## 🔧 Phân chia module

### 1. **main.py** - Entry Point
- Điểm vào chương trình
- Main loop xử lý menu
- Điều phối giữa các handlers
- **Chức năng**: Lightweight orchestrator (chỉ ~90 dòng)

### 2. **handlers.py** - Business Logic
- `handle_check_data()`: Kiểm tra filesystem và bitmap status
- `handle_corrupt_data()`: Phá hỏng bitmaps
- `handle_recover_data()`: Phục hồi directory tree và bitmaps
- `handle_show_details()`: Hiển thị thông tin chi tiết
- **Chức năng**: Xử lý tất cả logic nghiệp vụ

### 3. **utils.py** - Utilities
- `check_bitmap_corruption()`: Kiểm tra corruption
- `check_filesystem_status()`: Kiểm tra trạng thái tổng thể
- **Chức năng**: Các hàm tiện ích dùng chung

### 4. **ui.py** - User Interface
- `check_root()`: Kiểm tra quyền root
- `print_menu()`: Hiển thị menu
- **Chức năng**: Tất cả logic hiển thị UI

### 5. **bitmap_recovery.py** - Core Recovery
- `BitmapRecovery` class
- Load filesystem info (superblock, group descriptors)
- Corrupt/restore bitmaps
- Rebuild bitmaps từ inode data
- **Chức năng**: Core algorithm phục hồi bitmap

### 6. **directory_scanner.py** - Directory Recovery
- `DirectoryScanner` class
- Scan tất cả inodes
- Parse directory entries
- Rebuild directory tree
- Export file list
- **Chức năng**: Phục hồi cấu trúc thư mục

## 🔄 Luồng xử lý

```
main.py (entry point)
   │
   ├─> ui.py (print_menu, check_root)
   │
   ├─> handlers.py
   │    ├─> handle_check_data()
   │    │    ├─> directory_scanner.py (load filesystem info)
   │    │    ├─> bitmap_recovery.py (check bitmaps)
   │    │    └─> mount test
   │    │
   │    ├─> handle_corrupt_data()
   │    │    └─> bitmap_recovery.py (corrupt bitmaps)
   │    │
   │    ├─> handle_recover_data()
   │    │    ├─> directory_scanner.py (scan & rebuild tree)
   │    │    └─> bitmap_recovery.py (rebuild bitmaps)
   │    │
   │    └─> handle_show_details()
   │         └─> directory_scanner.py (show superblock/GDT)
   │
   └─> utils.py
        ├─> check_bitmap_corruption()
        └─> check_filesystem_status()
```

## ✨ Ưu điểm của cấu trúc mới

1. **Separation of Concerns**
   - UI logic riêng (ui.py)
   - Business logic riêng (handlers.py)
   - Utilities riêng (utils.py)
   - Core algorithms riêng (bitmap_recovery.py, directory_scanner.py)

2. **Maintainability**
   - main.py chỉ ~90 dòng, rất dễ đọc
   - Mỗi module có chức năng rõ ràng
   - Dễ debug và test từng module riêng

3. **Reusability**
   - handlers.py có thể tái sử dụng cho CLI khác
   - bitmap_recovery.py có thể dùng cho projects khác
   - utils.py cung cấp helpers chung

4. **Testability**
   - Mỗi module có thể test độc lập
   - Mock dependencies dễ dàng
   - Unit test cho từng function

5. **Scalability**
   - Thêm handler mới không ảnh hưởng main.py
   - Thêm utility functions vào utils.py
   - Mở rộng UI không ảnh hưởng logic

## 📊 So sánh với cấu trúc cũ

### Trước (main_old.py):
- 1 file lớn: 538 dòng
- Tất cả logic lẫn lộn
- Khó maintain và debug
- Khó tái sử dụng code

### Sau (modular):
- main.py: 90 dòng (entry point)
- handlers.py: ~450 dòng (business logic)
- utils.py: ~75 dòng (utilities)
- ui.py: ~50 dòng (UI)
- Tổng: 665 dòng nhưng tổ chức tốt hơn

## 🎯 Best Practices Applied

1. **Single Responsibility Principle**: Mỗi module một nhiệm vụ
2. **DRY (Don't Repeat Yourself)**: Utilities dùng chung
3. **Clean Code**: Functions ngắn, tên rõ ràng
4. **Modularity**: Dễ test, dễ maintain
5. **Documentation**: Comments rõ ràng ở mỗi function

## 🚀 Cách sử dụng

### Chạy chương trình:
```bash
sudo python3 main.py [image_file]
```

### Import modules riêng:
```python
from handlers import handle_check_data
from utils import check_filesystem_status
from bitmap_recovery import BitmapRecovery
```

### Test riêng từng module:
```python
# Test handlers
from handlers import handle_check_data
handle_check_data('test.img')

# Test utils
from utils import check_filesystem_status
status = check_filesystem_status('test.img')

# Test bitmap recovery
from bitmap_recovery import BitmapRecovery
bitmap = BitmapRecovery('test.img')
bitmap.load_filesystem_info()
```

## 📝 Tổng kết

Cấu trúc module mới:
- ✅ Dễ đọc, dễ hiểu
- ✅ Dễ maintain và debug
- ✅ Dễ mở rộng thêm tính năng
- ✅ Dễ test từng phần riêng
- ✅ Code reusable cao
- ✅ Follow best practices
