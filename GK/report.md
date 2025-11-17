**CHUYÊN ĐỀ: PHÂN TÍCH VÀ PHỤC HỒI HỆ THỐNG FILE EXT4 VỚI LỖI THAM SỐ VOLUME (HỎNG SUPERBLOCK)**

---

### 1. GIỚI THIỆU VẤN ĐỀ

Hệ thống file Ext4 (Fourth Extended Filesystem) là nền tảng lưu trữ mặc định trên đại đa số các bản phân phối Linux. Một trong những tình huống lỗi nghiêm trọng nhất là "sai tham số volume" (incorrect volume parameters). Về mặt kỹ thuật, lỗi này thường tương đương với việc **Superblock chính (Primary Superblock)** bị hỏng hoặc bị ghi đè.

Superblock là thành phần siêu dữ liệu (metadata) cốt lõi, hoạt động như "bảng thông số tổng" của toàn bộ volume. Khi nó bị hỏng, hệ điều hành không thể nhận diện hoặc mount (gắn) volume, dẫn đến việc mất khả năng truy cập toàn bộ dữ liệu, mặc dù bản thân dữ liệu thực tế (data blocks) có thể vẫn còn nguyên vẹn.

Báo cáo này tập trung phân tích lý thuyết về Superblock, cơ chế dự phòng của ext4, và trình bày một phương pháp luận phục hồi tự động để xử lý tình huống lỗi này.

**Implementation:** Dự án cung cấp hai phương pháp phục hồi:
1. **Python Script** (`recover_ext4.py`) - Giải pháp automation sử dụng e2fsck
2. **C++ Program** (`ext4_recovery`) - Low-level implementation với kiểm soát hoàn toàn

Chi tiết xem [INDEX.md](INDEX.md) và [COMPARISON.md](COMPARISON.md).

---

### 2. CƠ SỞ LÝ THUYẾT

#### 2.1. Cấu Trúc Block Group (Cụm Khối)

Một volume ext4 không phải là một khối lưu trữ đơn lẻ, mà được chia thành các **Cụm Khối (Block Group)** liền kề. Mỗi Block Group hoạt động như một hệ thống file thu nhỏ, chứa các thành phần riêng biệt:

* **Inode Table:** Bảng chứa các Inode (chỉ mục) lưu metadata của file (quyền, chủ sở hữu, con trỏ đến data blocks).
* **Data Blocks:** Nơi chứa dữ liệu thực tế của file.
* **Bitmaps:** Các bản đồ bit để theo dõi trạng thái "bận" hay "rảnh" của Inodes và Data Blocks.
* **Group Descriptors:** Bảng mô tả của chính Block Group đó.



Việc phân chia này giúp tối ưu hiệu suất bằng cách cố gắng lưu trữ Inode và Data Block của một file trong cùng một Group, giảm thiểu sự di chuyển của đầu đọc vật lý.

#### 2.2. Vai Trò Của Superblock
Superblock là một cấu trúc dữ liệu quan trọng, chứa các thông số toàn cục của hệ thống file. **Superblock chính** luôn nằm ở một vị trí cố định (offset 1024 bytes) trong **Block Group 0**.

Khi hệ điều hành thực hiện lệnh `mount`, nó sẽ đọc Superblock chính để lấy các tham số quan trọng:
* **Magic Number:** Một giá trị (ví dụ `0xEF53`) để xác nhận đây là hệ thống file ext4.
* **Block Size:** Kích thước của mỗi khối (phổ biến là 4096 bytes).
* **Total Blocks / Total Inodes:** Tổng số lượng khối và inode trên toàn volume.
* **Blocks per Group:** Số lượng khối trong mỗi Block Group.
* **Thông tin Journal:** Vị trí của vùng "nhật ký" (journal).

Nếu Superblock chính bị hỏng, Magic Number sẽ sai, Block Size bằng 0, và toàn bộ quá trình mount thất bại.

#### 2.3. Cơ Chế Dự Phòng (Redundancy) - Giải Pháp Của Ext4

Các nhà thiết kế ext4 nhận thức rõ Superblock chính là một **Điểm Lỗi Đơn Nhất (Single Point of Failure - SPOF)**.

Giải pháp của họ là cơ chế dự phòng: Hệ thống tự động **tạo ra các bản sao lưu (backup) của Superblock** và rải chúng vào các Block Group khác. Thông thường, các bản backup này được đặt ở đầu các Block Group có chỉ số 1, 3, 5, 7, v.v.

Quá trình `mke2fs` khi tạo file ảnh 1GB (đủ lớn để có nhiều Block Group) đã xác nhận điều này, cung cấp danh sách các backup tại các block: `32768`, `98304`, `163840`, `229376`,... (Đây là các vị trí block tiêu chuẩn cho block size 4k).

Đây chính là chìa khóa lý thuyết cho việc phục hồi: khi Superblock chính (Group 0) hỏng, dữ liệu vẫn an toàn và có thể được khôi phục bằng cách sử dụng một trong các bản sao lưu này.

---

### 3. PHÂN TÍCH TÌNH HUỐNG LỖI

Trong khuôn khổ thực nghiệm, lỗi "sai tham số" đã được tái tạo một cách có chủ đích để kiểm thử giải pháp.

#### 3.1. Tái Tạo Lỗi
Một file ảnh 1GB đã được định dạng ext4 và chứa file dữ liệu. Sau đó, lệnh `dd` được sử dụng để ghi 100 bytes dữ liệu rỗng (số 0) trực tiếp lên vị trí offset 1024:
`dd if=/dev/zero of=[image_file] bs=1 count=100 seek=1024 conv=notrunc`

Lệnh này mô phỏng chính xác việc Superblock chính bị ghi đè và hỏng.

#### 3.2. Triệu Chứng Lỗi
Các công cụ hệ thống tiêu chuẩn ngay lập tức thất bại khi tương tác với file ảnh hỏng:
1.  **Lệnh `mount`:** Thất bại với lỗi `bad superblock` hoặc `wrong fs type`, do không đọc được Magic Number hợp lệ.
2.  **Lệnh `e2fsck` (mặc định):** Thất bại với lỗi `Couldn't find valid filesystem superblock`, vì nó cũng tìm kiếm Superblock chính trước tiên.
3.  **Lệnh `mke2fs -n` (để tìm backup):** Thất bại. Đây là một phát hiện quan trọng, tạo ra một **vòng lặp Catch-22**. Lệnh `mke2fs` cũng cần đọc Superblock chính để xác định block size, trước khi nó có thể *tính toán* vị trí của các backup. Khi Superblock chính hỏng, nó cũng thất bại.

---

### 4. PHƯƠNG PHÁP LUẬN PHỤC HỒI

Giải pháp không phải là một lệnh đơn lẻ, mà là một kịch bản tự động hóa (robust script) mô phỏng quy trình xử lý của một kỹ sư hệ thống.

#### 4.1. Công Cụ Cốt Lõi: `e2fsck`
Tiện ích chính là `e2fsck` (một phần của `e2fsprogs`). Kỹ thuật phục hồi là sử dụng cờ `-b [block_number]`, ra lệnh cho `e2fsck` bỏ qua Superblock chính và sử dụng một Superblock dự phòng tại vị trí `[block_number]` làm nguồn thông tin.

#### 4.2. Thiết Kế Kịch Bản Phục Hồi Thông Minh
Kịch bản Python `recover_ext4_pro.py` được thiết kế để xử lý vấn đề một cách bền bỉ:

**1. Kế Hoạch A: Thử Tự Động**
* Kịch bản cố gắng chạy `mke2fs -n -F -b 4096 ...` để tự động dò tìm danh sách backup.
* Như đã phân tích ở (3.2), bước này được dự đoán là sẽ **thất bại** trong tình huống Superblock đã hỏng, và kịch bản đã xử lý ngoại lệ (exception) này.

**2. Kế Hoạch B: Chuyển sang Danh Sách Tiêu Chuẩn (Fallback)**
* Khi Kế hoạch A thất bại, kịch bản tự động chuyển sang Kế hoạch B.
* Nó sử dụng một danh sách "gán cứng" (hard-coded) các vị trí backup tiêu chuẩn đã biết: `STANDARD_BACKUP_BLOCKS = [32768, 98304, 163840, ...]`.
* Đây không phải là "đoán mò", mà là áp dụng kiến thức chuyên môn về tiêu chuẩn kỹ thuật của ext4 (với block size 4k).

**3. Vòng Lặp Phục Hồi Và Phân Tích Mã Lỗi**
* Kịch bản lặp qua danh sách `STANDARD_BACKUP_BLOCKS` và thử từng block.
* **Lần thử đầu tiên (block 32768):**
    * Thực thi: `e2fsck -f -y -b 32768 [image_file]`
    * `e2fsck` đọc bản backup "sạch" ở `32768`.
    * Nó so sánh với Superblock chính (đang hỏng) và các bitmaps.
    * Nó phát hiện hàng loạt sự không nhất quán (ví dụ: `Block bitmap differences...`, `Free blocks count wrong...`).
    * Do cờ `-y` (tự động Yes), `e2fsck` tiến hành "Fix" (sửa chữa). Hành động "Fix" quan trọng nhất là **ghi đè Superblock chính bị hỏng bằng dữ liệu từ bản backup tốt**.
    * `e2fsck` hoàn tất và trả về **Mã lỗi 1** (Return Code 1).
* Kịch bản phân tích mã lỗi: Mã 1 có nghĩa là "Lỗi đã được tìm thấy VÀ đã sửa chữa". Đây là tín hiệu thành công. Kịch bản ngay lập tức **dừng vòng lặp** (không cần thử `98304`).

**4. Bước 4: Xác Minh (Verification)**
* Sau khi sửa chữa thành công, kịch bản chạy `e2fsck -f -y [image_file]` một lần nữa, nhưng lần này **không dùng cờ `-b`**.
* Mục đích: Kiểm tra Superblock chính (vừa được phục hồi).
* Kết quả: `e2fsck` đọc Superblock chính mới, thấy nó hoàn toàn hợp lệ và nhất quán với phần còn lại của volume. Nó trả về **Mã lỗi 0** (Return Code 0), nghĩa là "Không có lỗi".