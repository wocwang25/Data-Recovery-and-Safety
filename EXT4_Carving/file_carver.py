import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_structures import EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE
from ext4_utils import EXT4Utils


# File signatures (magic bytes)
FILE_SIGNATURES = {
    'JPEG': {
        'header': b'\xFF\xD8\xFF',
        'footer': b'\xFF\xD9',
        'ext': '.jpg',
        'max_size': 20 * 1024 * 1024,
        'footer_extra_read': 1024,  # Read extra 1KB after footer for EXIF metadata
        'min_size': 10 * 1024  # JPEG files < 10KB are likely false positives (just thumbnails)
    },
    'PNG': {
        'header': b'\x89PNG\r\n\x1a\n',
        'footer': b'IEND\xAE\x42\x60\x82',
        'ext': '.png',
        'max_size': 10 * 1024 * 1024
    },
    'GIF': {
        'header': b'GIF8',
        'footer': b'\x00\x3B',
        'ext': '.gif',
        'max_size': 10 * 1024 * 1024
    },
    'PDF': {
        'header': b'%PDF-',
        'footer': b'%%EOF',
        'ext': '.pdf',
        'max_size': 50 * 1024 * 1024,
        'footer_offset': 10  # Allow extra bytes after %%EOF for newlines/whitespace
    },
    'ZIP': {
        'header': b'PK\x03\x04',
        'footer': b'PK\x05\x06',
        'ext': '.zip',
        'max_size': 100 * 1024 * 1024
    },
    'GZIP': {
        'header': b'\x1f\x8b\x08',
        'footer': None,
        'ext': '.gz',
        'max_size': 100 * 1024 * 1024
    },
    'MP3': {
        'header': b'\xFF\xFB',
        'footer': None,
        'ext': '.mp3',
        'max_size': 20 * 1024 * 1024,
        'min_blocks': 10  # MP3 files are usually multi-block, avoid tiny fragments
    },
    'MP4': {
        'header': b'\x00\x00\x00\x18ftyp',
        'footer': None,
        'ext': '.mp4',
        'max_size': 500 * 1024 * 1024
    },
    'AVI': {
        'header': b'RIFF',
        'footer': None,
        'ext': '.avi',
        'max_size': 500 * 1024 * 1024
    },
    'SQLITE': {
        'header': b'SQLite format 3\x00',
        'footer': None,
        'ext': '.db',
        'max_size': 100 * 1024 * 1024
    },
    'ELF': {
        'header': b'\x7fELF',
        'footer': None,
        'ext': '.elf',
        'max_size': 50 * 1024 * 1024
    },
    'TAR': {
        'header': b'ustar',
        'footer': None,
        'ext': '.tar',
        'max_size': 200 * 1024 * 1024
    },
}


class FileCarver:
    def __init__(self, image_file):
        self.image_file = image_file
        self.utils = EXT4Utils()
        self.superblock = None
        self.found_files = []
        
    def load_filesystem_info(self):
        sb_data = self.utils.read_bytes(self.image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
        if not sb_data:
            return False
            
        self.superblock = self.utils.parse_superblock(sb_data)
        if not self.superblock or not self.superblock.is_valid():
            return False
        
        return True
    
    def scan_data_blocks(self, start_block=0, end_block=None, progress_callback=None):
        if not self.superblock:
            return False
        
        block_size = self.superblock.get_block_size()
        total_blocks = self.superblock.get_total_blocks()
        
        if end_block is None or end_block > total_blocks:
            end_block = total_blocks
        
        print(f"\n Scanning blocks {start_block:,} to {end_block:,}...")
        print(f"   Block size: {block_size} bytes")
        print(f"   Total size: {(end_block - start_block) * block_size / 1024**2:.1f} MB")
        print(f"   Looking for: {len(FILE_SIGNATURES)} file types")
        print(f"   Note: Scans ALL blocks (both allocated and unallocated)")
        
        found_count = 0
        last_found_block = -1
        seen_signatures = set()  # Track để tránh duplicate files
        
        # Scan từng block
        for block_num in range(start_block, end_block):
            # Skip block nếu nằm trong file vừa tìm được (tránh duplicate)
            if block_num <= last_found_block:
                continue
            
            block_offset = block_num * block_size
            block_data = self.utils.read_bytes(self.image_file, block_offset, block_size)
            
            if not block_data:
                continue
            
            # Check xem block này có chứa file signature không
            for file_type, sig_info in FILE_SIGNATURES.items():
                header = sig_info['header']
                
                # Check header position (có thể ở đầu block hoặc offset 512)
                header_pos = block_data.find(header)
                
                if header_pos != -1 and header_pos < 512:  # Header phải gần đầu block
                    # Tìm thấy file header!
                    if progress_callback:
                        progress_callback(block_num, end_block, found_count, 
                                        f"Found {file_type} at block {block_num}")
                    
                    # Extract file data
                    file_data = self._extract_file(block_num, sig_info, header_pos)
                    
                    if file_data and len(file_data) > len(header):  # Phải có data thực sự
                        # Check duplicate bằng hash của 1KB đầu
                        file_hash = hash(bytes(file_data[:1024]))
                        if file_hash in seen_signatures:
                            # Skip duplicate file
                            continue
                        
                        seen_signatures.add(file_hash)
                        
                        self.found_files.append({
                            'type': file_type,
                            'start_block': block_num,
                            'size': len(file_data),
                            'data': file_data,
                            'ext': sig_info['ext']
                        })
                        found_count += 1
                        
                        # Update last found block để skip
                        blocks_used = (len(file_data) + block_size - 1) // block_size
                        last_found_block = block_num + blocks_used - 1
                        
                        if progress_callback:
                            progress_callback(block_num, end_block, found_count,
                                            f"Extracted {len(file_data):,} bytes")
                        
                        # Chỉ tìm 1 file type per block
                        break
            
            # Progress indicator mỗi 1000 blocks
            if block_num % 1000 == 0 and block_num > start_block:
                if progress_callback:
                    progress_callback(block_num, end_block, found_count, None)
        
        return True
    
    def _extract_file(self, start_block, sig_info, header_offset=0):
        block_size = self.superblock.get_block_size()
        max_size = sig_info['max_size']
        footer = sig_info['footer']
        
        data = bytearray()
        current_block = start_block
        first_block = True
        blocks_read = 0
        min_blocks = sig_info.get('min_blocks', 1)  # Minimum blocks to read
        max_blocks = 200  # Tăng lên để support larger files
        
        # Đọc blocks cho đến khi gặp footer hoặc đạt giới hạn
        while len(data) < max_size and blocks_read < max_blocks:
            block_offset = current_block * block_size
            block_data = self.utils.read_bytes(self.image_file, block_offset, block_size)
            
            if not block_data:
                break
            
            # Block đầu tiên: bỏ qua header_offset
            if first_block and header_offset > 0:
                block_data = block_data[header_offset:]
                first_block = False
            
            data.extend(block_data)
            blocks_read += 1
            
            # Nếu có footer, tìm nó NGAY sau mỗi block
            if footer:
                # CRITICAL FIX: Search footer trong vùng vừa đọc (bao gồm cả boundary giữa 2 blocks)
                # Tìm trong block cuối + 1 block trước đó để catch footer nằm giữa boundary
                # VD: Block 1 có "%%E", Block 2 có "OF" → footer nằm giữa
                if len(data) > len(block_data):
                    # Search từ (current_length - 2*block_size) để catch boundary cases
                    search_start = max(0, len(data) - len(block_data) - block_size)
                else:
                    # Block đầu tiên
                    search_start = 0
                footer_pos = data.find(footer, search_start)
                if footer_pos != -1:
                    # JPEG VALIDATION: Check if this is a real JPEG footer or false positive
                    if sig_info['ext'] == '.jpg':
                        # Strategy: JPEG có thể có FF D9 giả trong compressed data
                        # Chỉ chấp nhận footer nếu:
                        # 1. File đã đủ lớn (>= min_size)
                        # 2. Sau footer là padding HOẶC là end of data
                        # 3. HOẶC đã đọc đủ blocks (avoid infinite loop)
                        
                        current_size = footer_pos + len(footer)
                        min_size = sig_info.get('min_size', 0)
                        
                        # Rule 1: Nếu file quá nhỏ (<10KB), chắc chắn là false footer
                        if current_size < min_size and blocks_read < 10:
                            # Continue đọc thêm
                            current_block += 1
                            continue
                        
                        # Rule 2: Check context sau footer - CRITICAL for avoiding false positives
                        bytes_after_footer = len(data) - (footer_pos + len(footer))
                        
                        # ALWAYS validate footer context, even if little data after
                        # Check larger chunk (128 bytes) để chắc chắn
                        check_size = min(128, bytes_after_footer) if bytes_after_footer > 0 else 0
                        
                        if check_size > 0:
                            next_chunk = data[footer_pos + len(footer):footer_pos + len(footer) + check_size]
                            
                            # Check 3 điều kiện để ACCEPT footer:
                            # a) Có phải padding (00 hoặc FF) - ít nhất 60%
                            padding_count = sum(1 for b in next_chunk if b in (0, 255))
                            is_padding = padding_count > len(next_chunk) * 0.6
                            
                            # b) Có phải start of new file (JPEG/PNG/PDF header)
                            is_new_file = (len(next_chunk) >= 4 and (
                                          next_chunk[:3] == b'\xFF\xD8\xFF' or  # JPEG
                                          next_chunk[:4] == b'\x89PNG' or      # PNG
                                          next_chunk[:5] == b'%PDF-'))         # PDF
                            
                            # c) Đã đọc quá nhiều blocks rồi (>50) - force stop
                            too_many_blocks = blocks_read > 50
                            
                            # d) Gần end of data (<512 bytes after) - có thể là footer thật
                            near_end = bytes_after_footer < 512
                            
                            # ACCEPT footer nếu thỏa ít nhất 1 trong 4 điều kiện
                            should_accept = is_padding or is_new_file or too_many_blocks or near_end
                            
                            # REJECT footer → continue đọc
                            if not should_accept:
                                current_block += 1
                                continue
                        # Nếu không còn data sau footer → chắc chắn là footer thật
                    
                    # Check nếu cần đọc thêm data sau footer (for JPEG metadata)
                    footer_extra = sig_info.get('footer_extra_read', 0)
                    
                    if footer_extra > 0 and blocks_read < max_blocks:
                        # Đọc thêm 1 block nữa để capture metadata
                        need_extra = footer_pos + len(footer) + footer_extra - len(data)
                        if need_extra > 0:
                            current_block += 1
                            extra_block = self.utils.read_bytes(
                                self.image_file, 
                                current_block * block_size, 
                                block_size
                            )
                            if extra_block:
                                data.extend(extra_block)
                                blocks_read += 1
                    
                    # Tìm thấy footer, cắt data đến đó + extra offset
                    footer_offset = sig_info.get('footer_offset', 0)
                    end_pos = footer_pos + len(footer) + footer_offset + footer_extra
                    
                    # Đảm bảo không vượt quá data hiện tại
                    if end_pos > len(data):
                        end_pos = len(data)
                    
                    data = data[:end_pos]
                    
                    # Trim trailing whitespace/newlines cho PDF (nhưng giữ lại cấu trúc file)
                    if sig_info['ext'] == '.pdf':
                        # PDF footer có thể có whitespace nhưng KHÔNG NÊN có thêm > 100 bytes
                        # Tìm vị trí thực sự của %%EOF (có thể có \n\r sau nó)
                        trim_count = 0
                        while len(data) > footer_pos + len(footer) and trim_count < 100:
                            last_char = data[-1]
                            if last_char in (0, 10, 13, 32):  # null, \n, \r, space
                                data = data[:-1]
                                trim_count += 1
                            else:
                                break
                    
                    break
            
            # Nếu không có footer, detect ending differently
            else:
                # Đảm bảo đọc ít nhất min_blocks trước khi check padding
                if blocks_read < min_blocks:
                    current_block += 1
                    continue
                
                # Check padding cho non-MP3 files
                if sig_info['ext'] != '.mp3':
                    # Check 2 blocks cuối xem có phải padding không
                    if len(data) > block_size * 2:
                        last_2blocks = data[-block_size*2:]
                        zero_count = last_2blocks.count(0)
                        # Nếu > 80% là zeros → có thể đã hết data
                        if zero_count > len(last_2blocks) * 0.8:
                            break
                else:
                    # MP3: Continue until we hit another file header or excessive zeros
                    if len(data) > block_size * 4:
                        last_4blocks = data[-block_size*4:]
                        zero_count = last_4blocks.count(0)
                        # MP3 nên có ít zeros, nếu > 90% zeros → đã hết
                        if zero_count > len(last_4blocks) * 0.9:
                            break
            
            current_block += 1
        
        # Nếu không có footer, cắt tại chỗ data bắt đầu có nhiều zeros (padding)
        if not footer:
            data = self._trim_padding(data, max_size)
        
        return bytes(data) if len(data) > 0 else None
    
    def _trim_padding(self, data, max_size):
        # Nếu file quá lớn so với max_size → chắc chắn có padding
        if len(data) > max_size * 0.5:
            # Tìm vị trí bắt đầu có padding dài
            for i in range(len(data) - 1024, 0, -1024):
                chunk = data[i:i+1024]
                if chunk.count(0) < 512:  # < 50% zeros
                    # Đây là data thật, cắt tại đây
                    return data[:i+1024]
        
        # Fallback: trim zeros ở cuối
        last_nonzero = len(data) - 1
        zero_count = 0
        min_zero_streak = 2048  # Giảm threshold xuống 2KB
        
        while last_nonzero > 0 and zero_count < min_zero_streak:
            if data[last_nonzero] == 0:
                zero_count += 1
            else:
                zero_count = 0  # Reset counter
            last_nonzero -= 1
        
        # Cắt tại vị trí tìm được hoặc max_size (chọn nhỏ hơn)
        trim_pos = min(last_nonzero + min_zero_streak, max_size)
        return data[:trim_pos]
    
    def export_carved_files(self, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nExporting {len(self.found_files)} files to: {output_dir}")
        
        exported = 0
        for i, file_info in enumerate(self.found_files):
            filename = f"carved_{i+1:04d}_{file_info['type']}{file_info['ext']}"
            filepath = os.path.join(output_dir, filename)
            
            try:
                with open(filepath, 'wb') as f:
                    f.write(file_info['data'])
                
                print(f"   ✓ Exported: {filename} ({file_info['size']:,} bytes)")
                exported += 1
            except Exception as e:
                print(f"   ✗ Failed: {filename} - {e}")
        
        print(f"\n✓ Exported {exported}/{len(self.found_files)} files")
        return exported
    
    def print_summary(self):
        if not self.found_files:
            print("\nNo files found!")
            return
        
        print("\n" + "=" * 70)
        print("CARVED FILES SUMMARY")
        print("=" * 70)
        
        # Đếm theo loại
        type_count = {}
        total_size = 0
        
        for f in self.found_files:
            ftype = f['type']
            type_count[ftype] = type_count.get(ftype, 0) + 1
            total_size += f['size']
        
        print(f"\nTotal files found: {len(self.found_files)}")
        print(f"Total size: {total_size:,} bytes ({total_size / 1024**2:.2f} MB)")
        
        print("\nBy file type:")
        for ftype, count in sorted(type_count.items()):
            print(f"  {ftype:10s}: {count:3d} files")
        
        print("\n" + "=" * 70)
