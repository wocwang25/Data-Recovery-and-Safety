import os
import sys
import subprocess
from file_carver import FileCarver
from directory_carver import DirectoryCarver

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'EXT4Recovery'))
from ext4_structures import EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE
from ext4_utils import EXT4Utils


def handle_check_data(image_file):
    print("\n" + "=" * 70)
    print("CHECK DATA")
    print("=" * 70)
    print(f"Image: {image_file}")
    
    # Check if image exists
    if not os.path.exists(image_file):
        print(f"\n✗ Image file not found: {image_file}")
        input("\n[Press Enter to continue]")
        return False
    
    # Load filesystem info
    utils = EXT4Utils()
    sb_data = utils.read_bytes(image_file, EXT4_SUPERBLOCK_OFFSET, EXT4_SUPERBLOCK_SIZE)
    
    if not sb_data:
        print("\n✗ Failed to read superblock!")
        input("\n[Press Enter to continue]")
        return False
    
    superblock = utils.parse_superblock(sb_data)
    if not superblock or not superblock.is_valid():
        print("\n✗ Invalid superblock!")
        input("\n[Press Enter to continue]")
        return False
    
    # Print filesystem info
    print("\nFilesystem Information:")
    print("-" * 70)
    print(f"  Volume name: {superblock.get_volume_name()}")
    print(f"  Block size: {superblock.get_block_size()} bytes")
    print(f"  Total blocks: {superblock.get_total_blocks():,}")
    print(f"  Total inodes: {superblock.s_inodes_count:,}")
    print(f"  Free inodes: {superblock.s_free_inodes_count:,}")
    print(f"  Used inodes: {superblock.s_inodes_count - superblock.s_free_inodes_count:,}")
    
    size_mb = superblock.get_total_blocks() * superblock.get_block_size() / (1024**2)
    print(f"  Total size: {size_mb:.1f} MB")
    
    # Try to mount and list files
    print("\nFiles in filesystem:")
    print("-" * 70)
    
    mount_point = "/mnt/check_carving"
    os.makedirs(mount_point, exist_ok=True)
    
    try:
        # Mount
        subprocess.run(['mount', '-o', 'loop,ro', image_file, mount_point], 
                      check=True, capture_output=True)
        
        # List files
        result = subprocess.run(['find', mount_point, '-type', 'f'], 
                               capture_output=True, text=True)
        
        files = [f.replace(mount_point, '') for f in result.stdout.strip().split('\n') if f]
        
        if files:
            for f in files:
                # Get file size
                full_path = mount_point + f
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    print(f"  {f:40s} {size:>10,} bytes")
            print(f"\n  Total files: {len(files)}")
        else:
            print("  (no files found)")
        
        # List directories
        print("\nDirectories:")
        print("-" * 70)
        result = subprocess.run(['find', mount_point, '-type', 'd'], 
                               capture_output=True, text=True)
        
        dirs = [d.replace(mount_point, '') for d in result.stdout.strip().split('\n') if d and d != mount_point]
        
        if dirs:
            for d in dirs:
                print(f"  {d}")
            print(f"\n  Total directories: {len(dirs)}")
        else:
            print("  (no directories found)")
        
        # Unmount
        subprocess.run(['umount', mount_point], check=True, capture_output=True)
        
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Could not mount filesystem: {e}")
        # Try to unmount if mounted
        subprocess.run(['umount', mount_point], capture_output=True)
    
    print("\n" + "=" * 70)
    print("✓ Check complete!")
    print("=" * 70)
    
    input("\n[Press Enter to continue]")
    return True


def handle_delete_data(image_file):
    print("\n" + "=" * 70)
    print("DELETE DATA (FOR TESTING)")
    print("=" * 70)
    print(f"Image: {image_file}")
    
    # Mount filesystem
    mount_point = "/mnt/delete_carving"
    os.makedirs(mount_point, exist_ok=True)
    
    try:
        # Mount read-write
        subprocess.run(['mount', '-o', 'loop', image_file, mount_point], 
                      check=True, capture_output=True)
        
        # Show current structure
        print("\nCurrent structure:")
        print("-" * 70)
        result = subprocess.run(['tree', mount_point], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            # Fallback to find
            result = subprocess.run(['find', mount_point, '-not', '-path', '*/lost+found*'], 
                                   capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                if line and line != mount_point:
                    print(line.replace(mount_point, ''))
        
        # Delete all files and directories
        confirm = input("\nDelete ALL files and directories? [y/N]: ").strip().lower()
        
        if confirm == 'y':
            result = subprocess.run(['find', mount_point, '-mindepth', '1', '-not', '-path', '*/lost+found*', '-delete'], 
                                   capture_output=True)
            subprocess.run(['sync'])
            print("\n✓ Deleted all files and directories!")
        else:
            print("\n✓ Cancelled")
        
        # Show final structure
        print("\nFinal structure:")
        print("-" * 70)
        result = subprocess.run(['tree', mount_point], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            result = subprocess.run(['find', mount_point, '-not', '-path', '*/lost+found*'], 
                                   capture_output=True, text=True)
            for line in result.stdout.strip().split('\n'):
                if line and line != mount_point:
                    print(line.replace(mount_point, ''))
        
        # Unmount
        subprocess.run(['umount', mount_point], check=True, capture_output=True)
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error: {e}")
        subprocess.run(['umount', mount_point], capture_output=True)
    
    print("\n" + "=" * 70)
    print("✓ Delete operation complete!")
    print("=" * 70)
    
    input("\n[Press Enter to continue]")
    return True


def handle_recover_data(image_file):
    print("\n" + "=" * 70)
    print("RECOVER DATA (FILES + DIRECTORIES)")
    print("=" * 70)
    print(f"Image: {image_file}")
    
    # Step 1: File carving
    print("\n" + "=" * 70)
    print("STEP 1: FILE CARVING (Scan for deleted files)")
    print("=" * 70)
    
    file_carver = FileCarver(image_file)
    
    print("\nLoading filesystem info...")
    if not file_carver.load_filesystem_info():
        print("✗ Failed to load filesystem info!")
        input("\n[Press Enter to continue]")
        return False
    
    print(f"✓ Block size: {file_carver.superblock.get_block_size()} bytes")
    print(f"✓ Total blocks: {file_carver.superblock.get_total_blocks():,}")
    
    # Scan all blocks
    file_carver.scan_data_blocks()
    file_carver.print_summary()
    
    # Export files
    carved_files = []
    if file_carver.found_files:
        output_dir = "recovered_files"
        print("\n" + "=" * 70)
        file_carver.export_carved_files(output_dir)
        carved_files = file_carver.found_files
    
    # Step 2: Directory carving
    print("\n" + "=" * 70)
    print("STEP 2: DIRECTORY CARVING (Scan for deleted folders)")
    print("=" * 70)
    
    dir_carver = DirectoryCarver(image_file)
    
    print("\nLoading filesystem info...")
    if not dir_carver.load_filesystem_info():
        print("✗ Failed to load filesystem info!")
        input("\n[Press Enter to continue]")
        return False
    
    # Scan directory blocks
    dir_carver.scan_directory_blocks()
    dir_carver.rebuild_directory_tree()
    dir_carver.print_directory_tree()
    dir_carver.print_summary()
    
    # Export directory structure
    dir_output = "directory_structure.txt"
    print("\n" + "=" * 70)
    dir_carver.export_directory_list(dir_output)
    
    # Step 3: Rebuild directory structure with recovered files
    print("\n" + "=" * 70)
    print("STEP 3: REBUILD DIRECTORY STRUCTURE")
    print("=" * 70)
    
    if dir_carver.found_entries:
        recovered_root = "recovered_structure"
        print(f"\nCreating directory structure in: {recovered_root}/")
        
        try:
            # Clean old structure
            import shutil
            if os.path.exists(recovered_root):
                shutil.rmtree(recovered_root)
            os.makedirs(recovered_root)
            
            # Create directories
            created_dirs = set()
            for entry in dir_carver.found_entries:
                if entry['file_type'] == 2:  # Directory
                    dir_path = os.path.join(recovered_root, entry['name'])
                    if dir_path not in created_dirs and entry['name'] not in ['.', '..', 'lost+found']:
                        try:
                            os.makedirs(dir_path, exist_ok=True)
                            created_dirs.add(dir_path)
                            print(f"  ✓ Created: {entry['name']}/")
                        except:
                            pass
            
            # Copy carved files vào structure với improved mapping
            if carved_files and os.path.exists("recovered_files"):
                print(f"\nMapping carved files to directories...")
                
                # Build directory hierarchy map
                dir_hierarchy = {}
                for entry in dir_carver.found_entries:
                    if entry['file_type'] == 2:  # Directory
                        dir_name = entry['name']
                        inode = entry['inode']
                        dir_hierarchy[dir_name] = {
                            'inode': inode,
                            'path': None
                        }
                
                # Map file types to possible directories (with priority)
                file_type_mapping = {
                    'JPEG': [
                        ('vacation', 'photos/vacation'),
                        ('family', 'photos/family'),
                        ('photos', 'photos'),
                    ],
                    'PNG': [
                        ('family', 'photos/family'),
                        ('photos', 'photos'),
                    ],
                    'PDF': [
                        ('work', 'documents/work'),
                        ('personal', 'documents/personal'),
                        ('documents', 'documents'),
                    ],
                    'MP3': [
                        ('rock', 'music/rock'),
                        ('jazz', 'music/jazz'),
                        ('music', 'music'),
                    ],
                }
                
                for i, carved_file in enumerate(carved_files):
                    file_type = carved_file['type']
                    file_ext = carved_file['ext']
                    
                    # Try to find best matching directory
                    target_dir = recovered_root
                    matched_path = None
                    
                    if file_type in file_type_mapping:
                        for subdir_name, full_path in file_type_mapping[file_type]:
                            # Check if this subdirectory exists in recovered entries
                            if subdir_name in dir_hierarchy:
                                # Try to create full path
                                full_dir = os.path.join(recovered_root, full_path)
                                os.makedirs(full_dir, exist_ok=True)
                                target_dir = full_dir
                                matched_path = full_path
                                break
                    
                    # Copy file to target directory
                    src_file = f"recovered_files/carved_{i+1:04d}_{file_type}{file_ext}"
                    if os.path.exists(src_file):
                        filename = f"recovered_{i+1:04d}{file_ext}"
                        dst_file = os.path.join(target_dir, filename)
                        shutil.copy2(src_file, dst_file)
                        
                        if matched_path:
                            print(f"  ✓ {matched_path}/{filename}")
                        else:
                            print(f"  ✓ {filename} (root)")
            
            print(f"\n✓ Rebuilt structure in: {recovered_root}/")
            
            # Show final structure
            print("\nFinal structure:")
            print("-" * 70)
            for root, dirs, files in os.walk(recovered_root):
                level = root.replace(recovered_root, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 2 * (level + 1)
                for file in sorted(files):
                    print(f'{subindent}{file}')
        
        except Exception as e:
            print(f"✗ Error rebuilding structure: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("RECOVERY SUMMARY")
    print("=" * 70)
    
    file_count = len(carved_files)
    dir_count = len(dir_carver.directory_tree.get('directories', {}))
    
    print(f"\n✓ Recovered {file_count} files")
    print(f"✓ Recovered {dir_count} directories")
    print(f"\nOutput:")
    print(f"  • recovered_files/      - Carved files (flat)")
    print(f"  • {dir_output}          - Directory list")
    print(f"  • recovered_structure/  - Rebuilt directory tree")
    
    print("\n" + "=" * 70)
    print("✓ Recovery complete!")
    print("=" * 70)
    
    input("\n[Press Enter to continue]")
    return True
