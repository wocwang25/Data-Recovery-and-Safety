#!/bin/bash

# Script test công cụ phục hồi Ext4 C++
# Tạo image test, làm hỏng superblock, và test recovery

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     EXT4 RECOVERY TOOL - C++ VERSION TEST SCRIPT             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "[ERROR] Please run as root (sudo)"
    exit 1
fi

# Configuration
IMAGE_NAME="test_ext4_cpp.img"
IMAGE_SIZE_MB=100
MOUNT_POINT="/mnt/test_ext4_cpp"
TEST_FILE1="test_data_1.txt"
TEST_FILE2="test_data_2.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo ""
    echo -e "${GREEN}[STEP $1]${NC} $2"
    echo "----------------------------------------"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    umount "$MOUNT_POINT" 2>/dev/null || true
    rm -rf "$MOUNT_POINT"
    echo "Cleanup complete."
}

trap cleanup EXIT

# ============================================================================
# STEP 1: Build the C++ program
# ============================================================================
print_step 1 "Building C++ recovery tool"

if [ ! -f "ext4_recovery.cpp" ]; then
    print_error "ext4_recovery.cpp not found!"
    exit 1
fi

make clean 2>/dev/null || true
make

if [ ! -f "ext4_recovery" ]; then
    print_error "Build failed!"
    exit 1
fi

print_success "Build completed: ./ext4_recovery"

# ============================================================================
# STEP 2: Create test image
# ============================================================================
print_step 2 "Creating test Ext4 image (${IMAGE_SIZE_MB}MB)"

# Remove old image if exists
rm -f "$IMAGE_NAME"

# Create blank image
dd if=/dev/zero of="$IMAGE_NAME" bs=1M count=$IMAGE_SIZE_MB status=progress

# Format as Ext4
mkfs.ext4 -F "$IMAGE_NAME"

print_success "Image created: $IMAGE_NAME"

# ============================================================================
# STEP 3: Mount and add test data
# ============================================================================
print_step 3 "Adding test data to image"

# Create mount point
mkdir -p "$MOUNT_POINT"

# Mount
mount -o loop "$IMAGE_NAME" "$MOUNT_POINT"

# Create test files
echo "This is test file 1" > "$MOUNT_POINT/$TEST_FILE1"
echo "This is test file 2 - Important data!" > "$MOUNT_POINT/$TEST_FILE2"
echo "Line 1" > "$MOUNT_POINT/multiline.txt"
echo "Line 2" >> "$MOUNT_POINT/multiline.txt"
echo "Line 3" >> "$MOUNT_POINT/multiline.txt"

# Copy some system files for more realistic test
cp /etc/hosts "$MOUNT_POINT/" 2>/dev/null || true
cp /etc/passwd "$MOUNT_POINT/" 2>/dev/null || true

# List files
echo "Files in image:"
ls -lh "$MOUNT_POINT"

# Unmount
umount "$MOUNT_POINT"

print_success "Test data added successfully"

# ============================================================================
# STEP 4: Verify image is mountable (before corruption)
# ============================================================================
print_step 4 "Verifying image before corruption"

mount -o loop "$IMAGE_NAME" "$MOUNT_POINT"
if [ -f "$MOUNT_POINT/$TEST_FILE1" ]; then
    print_success "Image is valid and mountable"
    cat "$MOUNT_POINT/$TEST_FILE1"
else
    print_error "Image verification failed!"
    exit 1
fi
umount "$MOUNT_POINT"

# ============================================================================
# STEP 5: Corrupt the primary superblock
# ============================================================================
print_step 5 "Corrupting primary superblock (simulating error)"

print_warning "Writing zeros to superblock at offset 1024..."

# Corrupt superblock: write 100 bytes of zeros at offset 1024
dd if=/dev/zero of="$IMAGE_NAME" bs=1 count=100 seek=1024 conv=notrunc

print_success "Superblock corrupted"

# ============================================================================
# STEP 6: Verify corruption (mount should fail)
# ============================================================================
print_step 6 "Verifying corruption (mount should fail)"

if mount -o loop "$IMAGE_NAME" "$MOUNT_POINT" 2>/dev/null; then
    print_error "Mount succeeded when it should have failed!"
    umount "$MOUNT_POINT"
    exit 1
else
    print_success "Mount failed as expected - superblock is corrupted"
fi

# ============================================================================
# STEP 7: Analyze with C++ tool
# ============================================================================
print_step 7 "Analyzing corrupted image with C++ tool"

echo "Running: ./ext4_recovery $IMAGE_NAME"
echo ""
echo "Note: This will show the primary superblock is corrupted"
echo "Press Ctrl+C if you want to stop here"
echo ""
sleep 2

# We can't run interactive menu in script, so we'll test the code manually later
print_warning "Cannot run interactive menu in automated script"
print_warning "Please test manually after script completes"

# ============================================================================
# STEP 8: Instructions for manual testing
# ============================================================================
print_step 8 "Manual testing instructions"

echo "The image '$IMAGE_NAME' is now ready for testing."
echo ""
echo "To test the C++ recovery tool, run:"
echo ""
echo "  sudo ./ext4_recovery $IMAGE_NAME"
echo ""
echo "Then follow these steps:"
echo "  1. Choose option 1 to analyze primary superblock (should show corruption)"
echo "  2. Choose option 2 to scan backup superblocks"
echo "  3. Choose option 6 for full auto recovery"
echo "  4. Type 'I UNDERSTAND' when prompted"
echo "  5. Wait for recovery to complete"
echo ""
echo "After recovery, verify by mounting:"
echo ""
echo "  sudo mount -o loop $IMAGE_NAME $MOUNT_POINT"
echo "  ls -la $MOUNT_POINT"
echo "  cat $MOUNT_POINT/$TEST_FILE1"
echo "  sudo umount $MOUNT_POINT"
echo ""

# ============================================================================
# STEP 9: Alternative - Use Python recovery for comparison
# ============================================================================
print_step 9 "Alternative: Python recovery (for comparison)"

if [ -f "recover_ext4.py" ]; then
    echo "You can also test with Python version:"
    echo ""
    echo "  sudo python3 recover_ext4.py $IMAGE_NAME"
    echo ""
else
    print_warning "recover_ext4.py not found"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    TEST SETUP COMPLETE                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  - Image file: $IMAGE_NAME"
echo "  - Size: ${IMAGE_SIZE_MB}MB"
echo "  - Superblock: CORRUPTED (simulated error)"
echo "  - Test files: $TEST_FILE1, $TEST_FILE2, etc."
echo ""
echo "Next steps:"
echo "  1. Run: sudo ./ext4_recovery $IMAGE_NAME"
echo "  2. Test recovery"
echo "  3. Verify data integrity"
echo ""
echo "Good luck with your testing!"
