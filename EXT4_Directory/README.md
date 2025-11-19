# EXT4 Directory Recovery

Công cụ phục hồi dữ liệu khi bảng thư mục và block allocation bị hỏng.

## CƠ SỞ LÝ THUYẾT

### 1. Cấu trúc thư mục trong EXT4

**Directory trong EXT4** không phải là "bảng thư mục" riêng biệt như FAT32, mà là một **file đặc biệt** chứa danh sách các **directory entries**.

```
Directory = Special File chứa directory entries
├── Metadata: Inode (type = directory)
├── Data blocks: Chứa directory entries
└── Structure: Linear list hoặc HTree (hash tree)
```

**Mỗi directory entry** có cấu trúc:
```c
struct ext4_dir_entry_2 {
    __le32  inode;          // Inode number của file/dir
    __le16  rec_len;        // Chiều dài của entry này
    __u8    name_len;       // Độ dài tên file
    __u8    file_type;      // Loại: 1=file, 2=dir, 7=symlink
    char    name[255];      // Tên file (không null-terminated)
};
```

**Ví dụ thực tế:**
```
Root directory (inode 2) chứa:
├── [inode=11, type=2, name="."]        → Chính nó
├── [inode=2,  type=2, name=".."]       → Parent (root)
├── [inode=12, type=2, name="docs"]     → Thư mục docs
├── [inode=13, type=2, name="images"]   → Thư mục images
└── [inode=14, type=1, name="test.txt"] → File text
```

### 2. Bảng Cluster (Block Allocation) trong EXT4

**"Bảng Cluster"** trong EXT4 tương đương với **3 thành phần**:

#### 2.1. Block Bitmap
- **Mục đích:** Đánh dấu block nào đang được sử dụng, block nào còn trống
- **Cấu trúc:** 1 bit cho mỗi block (1 = used, 0 = free)
- **Vị trí:** Mỗi block group có 1 block bitmap riêng
- **Kích thước:** Block size / 8 bytes (ví dụ: 4096 / 8 = 512 bytes cho block size 4KB)

```
Block Bitmap của Group 0:
Bit 0-31:   [1111...1111] → Metadata blocks (superblock, GDT, bitmaps)
Bit 32-100: [1100...0001] → Một số blocks đang dùng
Bit 101+:   [0000...0000] → Các blocks trống
```

#### 2.2. Inode Bitmap
- **Mục đích:** Đánh dấu inode nào đang được sử dụng
- **Cấu trúc:** 1 bit cho mỗi inode (1 = allocated, 0 = free)
- **Vị trí:** Mỗi block group có 1 inode bitmap riêng

```
Inode Bitmap của Group 0:
Bit 0-10:  [1111...1111] → Reserved inodes (root, journal, etc.)
Bit 11-20: [1010...0001] → Một số inodes đang dùng
Bit 21+:   [0000...0000] → Các inodes trống
```

#### 2.3. Extent Tree (Block Mapping)
- **Mục đích:** Map logical blocks → physical blocks (file ở đâu trên đĩa)
- **Cấu trúc:** Tree structure lưu trong inode
- **Thay thế:** Block pointers trực tiếp (i_block[]) trong EXT2/3

```
Extent Header (12 bytes):
├── eh_magic:    0xF30A  (magic number)
├── eh_entries:  3       (số extents)
├── eh_max:      4       (max extents có thể chứa)
└── eh_depth:    0       (0 = leaf, >0 = internal node)

Extent Entry (12 bytes mỗi cái):
├── ee_block:    0       (logical block trong file)
├── ee_len:      100     (số blocks liên tiếp)
├── ee_start_hi: 0       (high 16-bit của physical block)
└── ee_start_lo: 32768   (low 32-bit của physical block)
   → File's block 0-99 map to disk blocks 32768-32867
```

### 3. Tình huống hỏng

#### Tình huống 1: Directory Corruption
**Nguyên nhân:**
- Ghi đè lên data blocks chứa directory entries
- Inode của directory bị corrupt (extent tree hỏng)
- Power failure trong lúc ghi directory

**Hậu quả:**
- `ls` không list được file/thư mục con
- Không truy cập được file (file not found)
- Directory tree bị đứt đoạn

**Ví dụ:**
```bash
$ ls /data/docs
ls: reading directory '.': Input/output error
# Directory entries bị corrupt, kernel không parse được
```

#### Tình huống 2: Block Bitmap Corruption
**Nguyên nhân:**
- Ghi đè lên block chứa bitmap
- Filesystem không được unmount đúng cách
- Lỗi hardware khi ghi bitmap

**Hậu quả:**
- Kernel nghĩ blocks đang dùng là trống → ghi đè lên dữ liệu cũ
- Hoặc nghĩ blocks trống là đang dùng → báo full disk sai
- `fsck` báo inconsistency

**Ví dụ:**
```bash
$ df -h
Filesystem      Size  Used Avail Use% 
/dev/sda1       100G   99G  1.0G  99%
# Thực tế còn nhiều trống nhưng bitmap sai
```

#### Tình huống 3: Inode Bitmap Corruption
**Nguyên nhân:** Tương tự block bitmap

**Hậu quả:**
- Không tạo được file mới (no free inodes)
- Hoặc tạo file ghi đè lên inode cũ → mất dữ liệu

#### Tình huống 4: Extent Tree Corruption
**Nguyên nhân:**
- Ghi đè lên extent data trong inode
- Inode bị corrupt một phần

**Hậu quả:**
- Không đọc được file content (I/O error)
- File size đúng nhưng đọc sai vị trí
- `cat file.txt` → Input/output error

## CÁCH PHỤC HỒI - CƠ SỞ LÝ THUYẾT

### 1. Phục hồi Directory Entries

**Nguyên lý:** Directory entries vẫn còn trong data blocks, chỉ cần parse lại

**Các bước:**
1. **Tìm root inode (inode 2):**
   - Vị trí cố định: `inode_table_block * block_size + 1 * inode_size`
   - Đọc extent tree để biết data blocks của root

2. **Parse directory entries từ data blocks:**
   ```python
   while offset < block_size:
       inode_num = read_4_bytes(offset)
       rec_len = read_2_bytes(offset + 4)
       name_len = read_1_byte(offset + 6)
       file_type = read_1_byte(offset + 7)
       name = read_bytes(offset + 8, name_len)
       
       if inode_num != 0:  # Valid entry
           entries.append({inode: inode_num, name: name, type: file_type})
       
       offset += rec_len
   ```

3. **Rebuild directory tree đệ quy:**
   - Với mỗi entry type=directory, đọc inode của nó
   - Parse directory entries của subdirectory
   - Tiếp tục đệ quy cho đến khi hết

**Lý do hoạt động:**
- Directory entries có `rec_len` và `inode != 0` để validate
- Có thể skip entries bị corrupt (rec_len = 0 hoặc quá lớn)
- Tree structure cho phép rebuild từ root xuống

### 2. Phục hồi Block Bitmap

**Nguyên lý:** Quét tất cả inodes đang dùng, đọc extent tree, rebuild bitmap

**Các bước:**

1. **Scan tất cả inodes trong inode table:**
   ```python
   for inode_num in range(1, total_inodes):
       inode = read_inode(inode_num)
       if inode.i_mode != 0:  # Inode đang được sử dụng
           valid_inodes.append(inode_num)
   ```

2. **Đọc extent tree của mỗi inode để lấy physical blocks:**
   ```python
   for inode_info in valid_inodes:
       extents = parse_extent_tree(inode_info.inode)
       for extent in extents:
           physical_start = extent.ee_start
           length = extent.ee_len
           # Mark blocks as used
           for block in range(physical_start, physical_start + length):
               set_bit_in_bitmap(block, 1)
   ```

3. **Mark metadata blocks:**
   ```python
   # Superblock, GDT, bitmaps, inode tables
   for group in groups:
       mark_used(group.superblock_block)
       mark_used(group.gdt_blocks)
       mark_used(group.block_bitmap_block)
       mark_used(group.inode_bitmap_block)
       mark_used(group.inode_table_blocks)
   ```

4. **Ghi bitmap mới lên disk:**
   ```python
   for group_num in range(num_groups):
       bitmap_offset = get_block_bitmap_offset(group_num)
       write_bytes(bitmap_offset, new_bitmap[group_num])
   ```

**Lý do hoạt động:**
- Extent tree lưu physical block locations
- Nếu inode còn nguyên, ta có thể rebuild toàn bộ block allocation
- Metadata blocks ở vị trí cố định theo group structure

### 3. Phục hồi Inode Bitmap

**Nguyên lý:** Scan inode table, đánh dấu inodes đang dùng

**Các bước:**

1. **Scan inode table:**
   ```python
   for inode_num in range(1, total_inodes):
       inode_offset = calculate_inode_offset(inode_num)
       inode = read_inode(inode_offset)
       
       if inode.i_mode != 0:  # Valid inode
           set_bit_in_inode_bitmap(inode_num, 1)
   ```

2. **Validate inodes:**
   ```python
   # Check i_mode has valid type bits
   if (inode.i_mode & S_IFMT) in [S_IFREG, S_IFDIR, S_IFLNK]:
       # Valid file type
   ```

**Lý do hoạt động:**
- Inode có `i_mode` field để identify file type
- `i_mode = 0` means inode is free
- Có thể distinguish valid inodes từ garbage data

### 4. Phục hồi Extent Tree (nếu bị hỏng)

**Nguyên lý:** Harder, cần heuristics để tìm data blocks

**Approaches:**

1. **Pattern matching:**
   - Scan disk tìm file signatures (magic numbers)
   - JPEG starts with `FF D8 FF`
   - PDF starts with `%PDF`

2. **Carving:**
   - Extract file từ raw disk data
   - Không cần filesystem structure

**Hạn chế:** Không thể khôi phục tên file và cấu trúc thư mục

## SO SÁNH VỚI FAT32

| Aspect | FAT32 | EXT4 |
|--------|-------|------|
| **Directory Structure** | FAT (File Allocation Table) - bảng liên kết clusters | Directory entries trong data blocks - không có bảng riêng |
| **"Bảng thư mục"** | Directory entries ở vị trí cố định | Directory = file đặc biệt, có inode |
| **"Bảng Cluster"** | FAT table - map cluster chains | Block bitmap + Inode bitmap + Extent tree |
| **Phục hồi khi hỏng** | Scan FAT table backup | Scan inodes + rebuild bitmaps |

### Tại sao EXT4 phức tạp hơn?
1. **Phân tán:** Metadata rải rác trong nhiều structures
2. **Linh hoạt:** Extent tree thay vì pointers đơn giản
3. **Hiệu quả:** Block groups giảm fragmentation nhưng tăng độ phức tạp

### Ưu điểm của cách tiếp cận EXT4:
1. **Hiệu năng cao:** Extent giảm overhead vs block pointers
2. **Scalability:** Hỗ trợ filesystems rất lớn (1 EB)
3. **Phục hồi tốt hơn:** Inodes chứa nhiều thông tin để validate

## IMPLEMENTATION - KỸ THUẬT CHI TIẾT

### 1. Directory Scanner

```python
class DirectoryScanner:
    def read_inode(self, inode_num):
        # Calculate inode location
        group = (inode_num - 1) // inodes_per_group
        local_idx = (inode_num - 1) % inodes_per_group
        
        inode_table_block = group_descriptors[group].bg_inode_table
        offset = inode_table_block * block_size + local_idx * inode_size
        
        return parse_inode(read_bytes(offset, inode_size))
    
    def parse_directory_block(self, data):
        entries = []
        offset = 0
        
        while offset < len(data):
            inode = read_u32(data, offset)
            rec_len = read_u16(data, offset + 4)
            name_len = read_u8(data, offset + 6)
            
            if inode != 0 and rec_len > 0:
                name = data[offset+8:offset+8+name_len]
                entries.append({'inode': inode, 'name': name})
            
            offset += rec_len
        
        return entries
```

### 2. Bitmap Recovery

```python
class BitmapRecovery:
    def rebuild_block_bitmap(self, inodes_data):
        # Initialize empty bitmap
        bitmap = bytearray(blocks_per_group // 8)
        
        # Mark metadata blocks
        mark_metadata_blocks(bitmap)
        
        # Parse extent tree of each inode
        for inode_info in inodes_data:
            extents = parse_extent_tree(inode_info.inode)
            
            for extent in extents:
                start_block = extent.ee_start
                num_blocks = extent.ee_len
                
                # Mark blocks as used
                for block in range(start_block, start_block + num_blocks):
                    set_bit(bitmap, block)
        
        return bitmap
```

### 3. Validation Techniques

**Kiểm tra Directory Entry hợp lệ:**
```python
def is_valid_dir_entry(entry):
    # Check inode number in valid range
    if entry.inode == 0 or entry.inode > total_inodes:
        return False
    
    # Check rec_len reasonable
    if entry.rec_len < 8 or entry.rec_len > block_size:
        return False
    
    # Check name_len matches rec_len
    min_len = 8 + entry.name_len
    if entry.rec_len < min_len:
        return False
    
    # Check file_type valid
    if entry.file_type not in [1, 2, 7]:  # file, dir, symlink
        return False
    
    return True
```

**Kiểm tra Inode hợp lệ:**
```python
def is_valid_inode(inode):
    # Check i_mode has valid file type
    file_type = inode.i_mode & 0xF000
    if file_type not in [0x8000, 0x4000, 0xA000]:  # reg, dir, link
        return False
    
    # Check timestamps reasonable (not 0, not in future)
    if inode.i_mtime == 0 or inode.i_mtime > current_time:
        return False
    
    # Check extent magic if using extents
    if inode.i_flags & EXT4_EXTENTS_FL:
        extent_header = parse_extent_header(inode.i_block)
        if extent_header.eh_magic != 0xF30A:
            return False
    
    return True
```

## Workflow Implementation

```
1. Kiểm tra dữ liệu test
   - Mount filesystem kiểm tra
   - List files/directories bằng ls
   - Verify bitmaps bằng dumpe2fs

2. Phá hỏng directory/bitmap
   - Backup trước khi corrupt
   - Ghi đè directory blocks bằng zeros
   - Ghi đè bitmaps bằng zeros

3. Quét và phục hồi
   - Scan 25600 inodes (100MB filesystem)
   - Parse extent trees
   - Rebuild 2 bitmaps (block + inode)
   - Verify bằng mount test

4. Kết quả
   - Filesystem có thể mount lại
   - Dữ liệu không bị mất
   - File structure được bảo toàn
```

## Files

- `main.py` - Menu chính
- `directory_scanner.py` - Quét và phục hồi directories  
- `bitmap_recovery.py` - Phục hồi block/inode bitmaps
- `ui.py` - Giao diện người dùng
- `test_auto.sh` - Test tự động

## Kết luận

**Khác biệt chính so với FAT32:**
- EXT4 phức tạp hơn nhưng robust hơn
- Có nhiều redundancy (group descriptors backup, etc.)
- Inode chứa đủ thông tin để rebuild filesystem

**Độ khó phục hồi:**
1. **Block/Inode bitmaps:** DỄ - chỉ cần scan inodes
2. **Directory entries:** TRUNG BÌNH - cần parse cẩn thận
3. **Extent trees:** KHÓ - cần heuristics nếu hoàn toàn hỏng
