import sys
import os
import struct

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_structures import EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE
from ext4_utils import EXT4Utils


class DirectoryCarver:
    def __init__(self, image_file):
        self.image_file = image_file
        self.utils = EXT4Utils()
        self.superblock = None
        self.found_entries = []
        self.directory_tree = {}
        
    def load_filesystem_info(self):
        sb_data = self.utils.read_bytes(self.image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
        if not sb_data:
            return False
            
        self.superblock = self.utils.parse_superblock(sb_data)
        if not self.superblock or not self.superblock.is_valid():
            return False
        
        return True
    
    def scan_directory_blocks(self):
        if not self.superblock:
            return False
        
        block_size = self.superblock.get_block_size()
        total_blocks = self.superblock.get_total_blocks()
        
        print(f"\nScanning {total_blocks:,} blocks for directory entries...")
        print(f"   Block size: {block_size} bytes")
        
        found_count = 0
        
        # Scan từng block
        for block_num in range(total_blocks):
            block_offset = block_num * block_size
            block_data = self.utils.read_bytes(self.image_file, block_offset, block_size)
            
            if not block_data:
                continue
            
            # Parse directory entries trong block này
            entries = self._parse_directory_entries(block_data, block_num)
            
            if entries:
                self.found_entries.extend(entries)
                found_count += len(entries)
            
            # Progress indicator
            if block_num % 1000 == 0 and block_num > 0:
                print(f"   Progress: {block_num:,}/{total_blocks:,} blocks ({found_count} entries)", end='\r')
        
        print(f"\n\n✓ Scan complete! Found {found_count} directory entries")
        return True
    
    def _parse_directory_entries(self, block_data, block_num):
        entries = []
        offset = 0
        
        while offset < len(block_data) - 8:
            # Parse entry header
            inode = struct.unpack('<I', block_data[offset:offset+4])[0]
            rec_len = struct.unpack('<H', block_data[offset+4:offset+6])[0]
            name_len = block_data[offset+6]
            file_type = block_data[offset+7]
            
            # Validate entry
            if not self._is_valid_entry(inode, rec_len, name_len, file_type):
                offset += 4  # Move forward and try again
                continue
            
            # Extract name
            if name_len > 0 and offset + 8 + name_len <= len(block_data):
                name_bytes = block_data[offset+8:offset+8+name_len]
                
                try:
                    name = name_bytes.decode('utf-8', errors='ignore')
                    
                    # Skip . and ..
                    if name not in ['.', '..'] and name.isprintable():
                        entries.append({
                            'block': block_num,
                            'inode': inode,
                            'name': name,
                            'file_type': file_type,
                            'file_type_str': self._get_file_type_str(file_type)
                        })
                except:
                    pass
            
            # Move to next entry
            if rec_len > 0:
                offset += rec_len
            else:
                offset += 4  # Avoid infinite loop
        
        return entries
    
    def _is_valid_entry(self, inode, rec_len, name_len, file_type):
        # Inode phải hợp lý (0 = unused entry, nhưng chấp nhận để tìm deleted)
        if inode > self.superblock.s_inodes_count:
            return False
        
        # rec_len phải hợp lý (tối thiểu 12 bytes, tối đa 1024)
        if rec_len < 12 or rec_len > 1024:
            return False
        
        # name_len phải hợp lý (tối đa 255)
        if name_len > 255:
            return False
        
        # file_type phải hợp lý (0-7)
        if file_type > 7:
            return False
        
        return True
    
    def _get_file_type_str(self, file_type):
        types = {
            0: 'Unknown',
            1: 'File',
            2: 'Directory',
            3: 'CharDev',
            4: 'BlockDev',
            5: 'FIFO',
            6: 'Socket',
            7: 'Symlink'
        }
        return types.get(file_type, 'Unknown')
    
    def rebuild_directory_tree(self):
        """
        Rebuild directory tree từ directory entries
        """
        print(f"\n🌳 Rebuilding directory tree...")
        
        # Group entries by inode (để tìm parent-child relationships)
        dirs = {}
        files = {}
        
        for entry in self.found_entries:
            if entry['file_type'] == 2:  # Directory
                if entry['inode'] not in dirs:
                    dirs[entry['inode']] = []
                dirs[entry['inode']].append(entry)
            elif entry['file_type'] == 1:  # File
                if entry['inode'] not in files:
                    files[entry['inode']] = []
                files[entry['inode']].append(entry)
        
        print(f"   Found {len(dirs)} unique directory inodes")
        print(f"   Found {len(files)} unique file inodes")
        
        # Build tree structure
        self.directory_tree = {
            'directories': dirs,
            'files': files
        }
        
        return True
    
    def print_directory_tree(self):
        print("\n" + "=" * 70)
        print("DIRECTORY TREE")
        print("=" * 70)
        
        # Print directories
        if self.directory_tree.get('directories'):
            print("\nDIRECTORIES:")
            for inode, entries in sorted(self.directory_tree['directories'].items()):
                # Có thể có nhiều entries cùng inode (deleted và tồn tại)
                names = list(set([e['name'] for e in entries]))
                print(f"   Inode {inode:6d}: {', '.join(names)}")
        
        # Print files
        if self.directory_tree.get('files'):
            print(f"\nFILES ({len(self.directory_tree['files'])} unique inodes):")
            
            # Group by name để dễ đọc
            name_groups = {}
            for inode, entries in self.directory_tree['files'].items():
                for entry in entries:
                    name = entry['name']
                    if name not in name_groups:
                        name_groups[name] = []
                    name_groups[name].append(inode)
            
            # Print by name
            for name in sorted(name_groups.keys()):
                inodes = name_groups[name]
                if len(inodes) == 1:
                    print(f"   {name:30s} (inode {inodes[0]})")
                else:
                    print(f"   {name:30s} (inodes {', '.join(map(str, inodes))})")
    
    def export_directory_list(self, output_file):
        print(f"\nExporting directory list to: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("RECOVERED DIRECTORY STRUCTURE\n")
            f.write("=" * 70 + "\n\n")
            
            # Directories
            if self.directory_tree.get('directories'):
                f.write("DIRECTORIES:\n")
                f.write("-" * 70 + "\n")
                for inode, entries in sorted(self.directory_tree['directories'].items()):
                    names = list(set([e['name'] for e in entries]))
                    f.write(f"Inode {inode:6d}: {', '.join(names)}\n")
                f.write("\n")
            
            # Files
            if self.directory_tree.get('files'):
                f.write(f"FILES ({len(self.directory_tree['files'])} unique inodes):\n")
                f.write("-" * 70 + "\n")
                
                # Group by name
                name_groups = {}
                for inode, entries in self.directory_tree['files'].items():
                    for entry in entries:
                        name = entry['name']
                        if name not in name_groups:
                            name_groups[name] = []
                        name_groups[name].append(inode)
                
                # Write by name
                for name in sorted(name_groups.keys()):
                    inodes = name_groups[name]
                    if len(inodes) == 1:
                        f.write(f"{name:40s} inode {inodes[0]}\n")
                    else:
                        f.write(f"{name:40s} inodes {', '.join(map(str, inodes))}\n")
        
        print(f"✓ Exported to {output_file}")
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("DIRECTORY CARVING SUMMARY")
        print("=" * 70)
        
        total_entries = len(self.found_entries)
        dir_count = len(self.directory_tree.get('directories', {}))
        file_count = len(self.directory_tree.get('files', {}))
        
        print(f"\nTotal directory entries found: {total_entries:,}")
        print(f"Unique directory inodes: {dir_count}")
        print(f"Unique file inodes: {file_count}")
        
        # Count by file type
        type_count = {}
        for entry in self.found_entries:
            ftype = entry['file_type_str']
            type_count[ftype] = type_count.get(ftype, 0) + 1
        
        print("\nBy entry type:")
        for ftype, count in sorted(type_count.items()):
            print(f"  {ftype:15s}: {count:5d} entries")
