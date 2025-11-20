#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

IMAGE="test_recovery.img"
SIZE_MB=100
MOUNT_POINT="/mnt/test_recovery"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}           EXT4 FILE CARVING - Test Image Creation${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Cleanup
echo -e "\n${YELLOW}[1/7] Cleanup...${NC}"
if mount | grep -q "$MOUNT_POINT"; then
    umount "$MOUNT_POINT" 2>/dev/null || true
fi
rm -f "$IMAGE"
rm -rf recovered_files recovered_structure directory_structure.txt
mkdir -p "$MOUNT_POINT"
echo -e "${GREEN}✓ Cleaned up${NC}"

# Create image
echo -e "\n${YELLOW}[2/7] Creating ${SIZE_MB}MB image...${NC}"
dd if=/dev/zero of="$IMAGE" bs=1M count=$SIZE_MB status=none
echo -e "${GREEN}✓ Created $IMAGE (${SIZE_MB} MB)${NC}"

# Format
echo -e "\n${YELLOW}[3/7] Formatting with EXT4...${NC}"
mkfs.ext4 -F -L "TestRecovery" "$IMAGE" > /dev/null 2>&1
echo -e "${GREEN}✓ Formatted with EXT4${NC}"

# Mount
echo -e "\n${YELLOW}[4/7] Mounting filesystem...${NC}"
mount -o loop "$IMAGE" "$MOUNT_POINT"
echo -e "${GREEN}✓ Mounted at $MOUNT_POINT${NC}"

# Create directory structure
echo -e "\n${YELLOW}[5/7] Creating directory structure...${NC}"
mkdir -p "$MOUNT_POINT/photos/vacation"
mkdir -p "$MOUNT_POINT/photos/family"
mkdir -p "$MOUNT_POINT/documents/work"
mkdir -p "$MOUNT_POINT/documents/personal"
mkdir -p "$MOUNT_POINT/music/rock"
mkdir -p "$MOUNT_POINT/music/jazz"
mkdir -p "$MOUNT_POINT/videos"
echo -e "${GREEN}✓ Created directories${NC}"

# Create test files with valid signatures
echo -e "\n${YELLOW}[5/7] Creating test files...${NC}"

# Photos in vacation folder
printf '\xFF\xD8\xFF\xE0\x00\x10JFIF' > "$MOUNT_POINT/photos/vacation/beach1.jpg"
dd if=/dev/urandom bs=1024 count=80 2>/dev/null >> "$MOUNT_POINT/photos/vacation/beach1.jpg"
printf '\xFF\xD9' >> "$MOUNT_POINT/photos/vacation/beach1.jpg"
echo -e "  ${GREEN}✓${NC} photos/vacation/beach1.jpg (80 KB)"

printf '\xFF\xD8\xFF\xE0\x00\x10JFIF' > "$MOUNT_POINT/photos/vacation/beach2.jpg"
dd if=/dev/urandom bs=1024 count=60 2>/dev/null >> "$MOUNT_POINT/photos/vacation/beach2.jpg"
printf '\xFF\xD9' >> "$MOUNT_POINT/photos/vacation/beach2.jpg"
echo -e "  ${GREEN}✓${NC} photos/vacation/beach2.jpg (60 KB)"

# Photos in family folder
printf '\xFF\xD8\xFF\xE0\x00\x10JFIF' > "$MOUNT_POINT/photos/family/kids.jpg"
dd if=/dev/urandom bs=1024 count=50 2>/dev/null >> "$MOUNT_POINT/photos/family/kids.jpg"
printf '\xFF\xD9' >> "$MOUNT_POINT/photos/family/kids.jpg"
echo -e "  ${GREEN}✓${NC} photos/family/kids.jpg (50 KB)"

printf '\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR' > "$MOUNT_POINT/photos/family/portrait.png"
dd if=/dev/urandom bs=1024 count=40 2>/dev/null >> "$MOUNT_POINT/photos/family/portrait.png"
printf 'IEND\xAE\x42\x60\x82' >> "$MOUNT_POINT/photos/family/portrait.png"
echo -e "  ${GREEN}✓${NC} photos/family/portrait.png (40 KB)"

# Documents in work folder
printf '%%PDF-1.5\n' > "$MOUNT_POINT/documents/work/report.pdf"
dd if=/dev/urandom bs=1024 count=150 2>/dev/null >> "$MOUNT_POINT/documents/work/report.pdf"
printf '\n%%EOF' >> "$MOUNT_POINT/documents/work/report.pdf"
echo -e "  ${GREEN}✓${NC} documents/work/report.pdf (150 KB)"

printf '%%PDF-1.4\n' > "$MOUNT_POINT/documents/work/presentation.pdf"
dd if=/dev/urandom bs=1024 count=200 2>/dev/null >> "$MOUNT_POINT/documents/work/presentation.pdf"
printf '\n%%EOF' >> "$MOUNT_POINT/documents/work/presentation.pdf"
echo -e "  ${GREEN}✓${NC} documents/work/presentation.pdf (200 KB)"

# Documents in personal folder
printf '%%PDF-1.5\n' > "$MOUNT_POINT/documents/personal/notes.pdf"
dd if=/dev/urandom bs=1024 count=100 2>/dev/null >> "$MOUNT_POINT/documents/personal/notes.pdf"
printf '\n%%EOF' >> "$MOUNT_POINT/documents/personal/notes.pdf"
echo -e "  ${GREEN}✓${NC} documents/personal/notes.pdf (100 KB)"

# Music files
printf '\xFF\xFB\x90\x00' > "$MOUNT_POINT/music/rock/song1.mp3"
dd if=/dev/urandom bs=1024 count=500 2>/dev/null >> "$MOUNT_POINT/music/rock/song1.mp3"
echo -e "  ${GREEN}✓${NC} music/rock/song1.mp3 (500 KB)"

printf '\xFF\xFB\x90\x00' > "$MOUNT_POINT/music/jazz/jazz1.mp3"
dd if=/dev/urandom bs=1024 count=400 2>/dev/null >> "$MOUNT_POINT/music/jazz/jazz1.mp3"
echo -e "  ${GREEN}✓${NC} music/jazz/jazz1.mp3 (400 KB)"

# Sync to ensure all data is written
sync

# Show structure after deletion
echo -e "\n${CYAN}Structure: ${NC}"
tree "$MOUNT_POINT" -h 2>/dev/null || find "$MOUNT_POINT" -type f -not -path "*/lost+found/*" | sed "s|$MOUNT_POINT||"

REMAINING_FILES=$(find "$MOUNT_POINT" -type f -not -path "*/lost+found/*" | wc -l)
REMAINING_DIRS=$(find "$MOUNT_POINT" -type d -not -path "*/lost+found*" | wc -l)

# Sync again
sync
sleep 1

# Unmount
echo -e "\n${YELLOW}[7/7] Unmounting...${NC}"
umount "$MOUNT_POINT"
echo -e "${GREEN}✓ Unmounted${NC}"

# Summary
echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${GREEN}✓ Test image created: $IMAGE${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "\n${CYAN}Created:${NC}"
echo -e "  • ${TOTAL_FILES} files in ${TOTAL_DIRS} directories"
# echo -e "\n${RED}Deleted:${NC}"
# echo -e "  • ${DELETED_FILES} files"
# echo -e "  • ${DELETED_DIRS} directories (photos/vacation, documents/work)"
# echo -e "\n${GREEN}Remaining:${NC}"
# echo -e "  • ${REMAINING_FILES} files in ${REMAINING_DIRS} directories"
# echo -e "\n${YELLOW}Expected recovery:${NC}"
# echo -e "  • ${DELETED_FILES} deleted files + ${REMAINING_FILES} existing files"
# echo -e "  • ${DELETED_DIRS} deleted directories + ${REMAINING_DIRS} existing directories"
echo -e "\n${BLUE}======================================================================${NC}"

echo -e "\n${CYAN}Test file carving with:${NC}"
echo -e "  ${YELLOW}sudo python3 main.py${NC}"
