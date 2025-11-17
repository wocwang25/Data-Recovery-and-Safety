#include "ext4_recovery.h"
#include <ctime>
#include <algorithm>

// ============================================================================
// Ext4Utils Namespace Implementation
// ============================================================================

namespace Ext4Utils {
    string bytesToHex(const uint8_t* bytes, size_t length) {
        stringstream ss;
        ss << hex << setfill('0');
        for (size_t i = 0; i < length; i++) {
            ss << setw(2) << static_cast<int>(bytes[i]);
        }
        return ss.str();
    }
    
    string formatBlockSize(uint32_t blockSize) {
        if (blockSize >= 1024 * 1024) {
            return to_string(blockSize / (1024 * 1024)) + " MB";
        } else if (blockSize >= 1024) {
            return to_string(blockSize / 1024) + " KB";
        }
        return to_string(blockSize) + " B";
    }
    
    string formatTimestamp(uint32_t timestamp) {
        time_t rawtime = static_cast<time_t>(timestamp);
        struct tm* timeinfo = localtime(&rawtime);
        char buffer[80];
        strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", timeinfo);
        return string(buffer);
    }
    
    bool isValidMagic(uint16_t magic) {
        return magic == EXT4_MAGIC;
    }
    
    uint64_t calculateBlockOffset(uint64_t blockNumber, uint32_t blockSize) {
        return blockNumber * blockSize + EXT4_SUPERBLOCK_OFFSET;
    }
}

// ============================================================================
// Ext4Recovery Class Implementation
// ============================================================================

Ext4Recovery::Ext4Recovery(const string& device) 
    : devicePath(device), deviceFd(-1), deviceOpened(false) {
    memset(&primarySuperblock, 0, sizeof(Ext4Superblock));
}

Ext4Recovery::~Ext4Recovery() {
    _closeDevice();
}

bool Ext4Recovery::_openDevice() {
    if (deviceOpened) {
        return true;
    }
    
    deviceFd = open(devicePath.c_str(), O_RDWR);
    if (deviceFd < 0) {
        cerr << "[ERROR] Cannot open device: " << devicePath << endl;
        cerr << "        Make sure you have root permission and the path is correct." << endl;
        return false;
    }
    
    deviceOpened = true;
    cout << "[INFO] Device opened successfully: " << devicePath << endl;
    return true;
}

void Ext4Recovery::_closeDevice() {
    if (deviceOpened && deviceFd >= 0) {
        close(deviceFd);
        deviceFd = -1;
        deviceOpened = false;
        cout << "[INFO] Device closed." << endl;
    }
}

bool Ext4Recovery::_readSuperblock(uint64_t blockNumber, Ext4Superblock& sb) {
    if (!deviceOpened && !_openDevice()) {
        return false;
    }
    
    // Calculate offset
    uint64_t offset;
    if (blockNumber == 0) {
        // Primary superblock at offset 1024
        offset = EXT4_SUPERBLOCK_OFFSET;
    } else {
        // Backup superblocks
        offset = blockNumber * BLOCK_SIZE_4K + EXT4_SUPERBLOCK_OFFSET;
    }
    
    // Seek to position
    if (lseek(deviceFd, offset, SEEK_SET) < 0) {
        cerr << "[ERROR] Failed to seek to offset " << offset << endl;
        return false;
    }
    
    // Read superblock
    ssize_t bytesRead = read(deviceFd, &sb, sizeof(Ext4Superblock));
    if (bytesRead != sizeof(Ext4Superblock)) {
        cerr << "[ERROR] Failed to read superblock at block " << blockNumber << endl;
        return false;
    }
    
    return true;
}

bool Ext4Recovery::_writeSuperblock(uint64_t blockNumber, const Ext4Superblock& sb) {
    if (!deviceOpened && !_openDevice()) {
        return false;
    }
    
    // Calculate offset
    uint64_t offset;
    if (blockNumber == 0) {
        offset = EXT4_SUPERBLOCK_OFFSET;
    } else {
        offset = blockNumber * BLOCK_SIZE_4K + EXT4_SUPERBLOCK_OFFSET;
    }
    
    // Seek to position
    if (lseek(deviceFd, offset, SEEK_SET) < 0) {
        cerr << "[ERROR] Failed to seek to offset " << offset << endl;
        return false;
    }
    
    // Write superblock
    ssize_t bytesWritten = write(deviceFd, &sb, sizeof(Ext4Superblock));
    if (bytesWritten != sizeof(Ext4Superblock)) {
        cerr << "[ERROR] Failed to write superblock at block " << blockNumber << endl;
        return false;
    }
    
    // Sync to disk
    fsync(deviceFd);
    
    return true;
}

bool Ext4Recovery::_verifySuperblock(const Ext4Superblock& sb) {
    // Check magic number
    if (!Ext4Utils::isValidMagic(sb.s_magic)) {
        return false;
    }
    
    // Check basic sanity
    if (sb.s_inodes_count == 0 || sb.s_blocks_count_lo == 0) {
        return false;
    }
    
    if (sb.s_inodes_per_group == 0 || sb.s_blocks_per_group == 0) {
        return false;
    }
    
    // Block size should be reasonable (1K, 2K, 4K, 8K, ...)
    uint32_t blockSize = 1024 << sb.s_log_block_size;
    if (blockSize < 1024 || blockSize > 65536) {
        return false;
    }
    
    return true;
}

void Ext4Recovery::_calculateBackupLocations(uint32_t blockSize) {
    backupBlockLocations.clear();
    
    // Standard backup locations for 4K block size
    // These are at the start of block groups 1, 3, 5, 7, 9, ...
    vector<uint64_t> standardBackups = {32768, 98304, 163840, 229376, 294912, 
                                         360448, 425984, 491520, 557056, 622592};
    
    backupBlockLocations = standardBackups;
}

uint32_t Ext4Recovery::_getBlockSize(const Ext4Superblock& sb) {
    return 1024 << sb.s_log_block_size;
}

bool Ext4Recovery::_compareSuperblocks(const Ext4Superblock& sb1, const Ext4Superblock& sb2) {
    // Compare critical fields
    if (sb1.s_magic != sb2.s_magic) return false;
    if (sb1.s_inodes_count != sb2.s_inodes_count) return false;
    if (sb1.s_blocks_count_lo != sb2.s_blocks_count_lo) return false;
    if (sb1.s_blocks_per_group != sb2.s_blocks_per_group) return false;
    if (sb1.s_inodes_per_group != sb2.s_inodes_per_group) return false;
    if (sb1.s_log_block_size != sb2.s_log_block_size) return false;
    
    // Compare UUID
    if (memcmp(sb1.s_uuid, sb2.s_uuid, 16) != 0) return false;
    
    return true;
}

void Ext4Recovery::_printSuperblockInfo(const Ext4Superblock& sb, const string& label) {
    cout << "\n========== " << label << " ==========" << endl;
    cout << "Magic Number:      0x" << hex << sb.s_magic << dec;
    if (Ext4Utils::isValidMagic(sb.s_magic)) {
        cout << " (VALID)" << endl;
    } else {
        cout << " (INVALID - should be 0xEF53)" << endl;
    }
    
    cout << "Inodes Count:      " << sb.s_inodes_count << endl;
    cout << "Blocks Count:      " << sb.s_blocks_count_lo << endl;
    cout << "Free Blocks:       " << sb.s_free_blocks_count_lo << endl;
    cout << "Free Inodes:       " << sb.s_free_inodes_count << endl;
    cout << "Block Size:        " << _getBlockSize(sb) << " bytes" << endl;
    cout << "Blocks per Group:  " << sb.s_blocks_per_group << endl;
    cout << "Inodes per Group:  " << sb.s_inodes_per_group << endl;
    cout << "Inode Size:        " << sb.s_inode_size << " bytes" << endl;
    cout << "Volume Name:       ";
    for (int i = 0; i < 16 && sb.s_volume_name[i] != '\0'; i++) {
        cout << sb.s_volume_name[i];
    }
    cout << endl;
    cout << "UUID:              " << Ext4Utils::bytesToHex(sb.s_uuid, 16) << endl;
    cout << "Last Mount:        " << Ext4Utils::formatTimestamp(sb.s_mtime) << endl;
    cout << "Last Write:        " << Ext4Utils::formatTimestamp(sb.s_wtime) << endl;
    cout << "Mount Count:       " << sb.s_mnt_count << endl;
    cout << "State:             " << sb.s_state << endl;
    cout << "=====================================" << endl;
}

// ============================================================================
// Public Methods
// ============================================================================

bool Ext4Recovery::analyzePrimarySuperblock() {
    cout << "\n[STEP 1] Analyzing Primary Superblock..." << endl;
    
    if (!_readSuperblock(0, primarySuperblock)) {
        cerr << "[ERROR] Failed to read primary superblock!" << endl;
        return false;
    }
    
    _printSuperblockInfo(primarySuperblock, "PRIMARY SUPERBLOCK");
    
    bool isValid = _verifySuperblock(primarySuperblock);
    if (isValid) {
        cout << "\n[RESULT] Primary superblock appears to be VALID." << endl;
        cout << "         No recovery needed." << endl;
        return true;
    } else {
        cout << "\n[RESULT] Primary superblock is CORRUPTED!" << endl;
        cout << "         Recovery is needed." << endl;
        
        // Calculate backup locations based on standard 4K block size
        _calculateBackupLocations(BLOCK_SIZE_4K);
        return false;
    }
}

bool Ext4Recovery::scanBackupSuperblocks() {
    cout << "\n[STEP 2] Scanning Backup Superblocks..." << endl;
    
    if (backupBlockLocations.empty()) {
        _calculateBackupLocations(BLOCK_SIZE_4K);
    }
    
    int validCount = 0;
    int invalidCount = 0;
    
    for (size_t i = 0; i < backupBlockLocations.size(); i++) {
        uint64_t blockNum = backupBlockLocations[i];
        Ext4Superblock backupSb;
        
        cout << "\n--- Checking backup at block " << blockNum << " ---" << endl;
        
        if (!_readSuperblock(blockNum, backupSb)) {
            cout << "[FAILED] Could not read backup superblock" << endl;
            invalidCount++;
            continue;
        }
        
        bool isValid = _verifySuperblock(backupSb);
        if (isValid) {
            cout << "[VALID] Magic: 0x" << hex << backupSb.s_magic << dec << endl;
            cout << "        Inodes: " << backupSb.s_inodes_count << endl;
            cout << "        Blocks: " << backupSb.s_blocks_count_lo << endl;
            validCount++;
        } else {
            cout << "[INVALID] Backup superblock is corrupted" << endl;
            invalidCount++;
        }
    }
    
    cout << "\n[SUMMARY] Valid backups: " << validCount 
         << ", Invalid: " << invalidCount << endl;
    
    return validCount > 0;
}

bool Ext4Recovery::findBestBackup(Ext4Superblock& bestBackup, uint64_t& bestBlockLocation) {
    cout << "\n[STEP 3] Finding Best Backup Superblock..." << endl;
    
    if (backupBlockLocations.empty()) {
        _calculateBackupLocations(BLOCK_SIZE_4K);
    }
    
    // Find the first valid backup
    for (uint64_t blockNum : backupBlockLocations) {
        Ext4Superblock backupSb;
        
        if (_readSuperblock(blockNum, backupSb) && _verifySuperblock(backupSb)) {
            bestBackup = backupSb;
            bestBlockLocation = blockNum;
            
            cout << "[SUCCESS] Found valid backup at block " << blockNum << endl;
            _printSuperblockInfo(bestBackup, "BEST BACKUP SUPERBLOCK");
            return true;
        }
    }
    
    cerr << "[ERROR] No valid backup superblock found!" << endl;
    return false;
}

bool Ext4Recovery::repairPrimarySuperblock() {
    cout << "\n[STEP 4] Repairing Primary Superblock..." << endl;
    
    Ext4Superblock bestBackup;
    uint64_t bestBlockLocation;
    
    if (!findBestBackup(bestBackup, bestBlockLocation)) {
        return false;
    }
    
    // Create backup before writing
    cout << "\n[INFO] Creating backup of corrupted superblock..." << endl;
    string backupFile = devicePath + ".corrupted_sb.backup";
    ofstream backup(backupFile, ios::binary);
    if (backup.is_open()) {
        backup.write(reinterpret_cast<const char*>(&primarySuperblock), 
                     sizeof(Ext4Superblock));
        backup.close();
        cout << "[INFO] Backup saved to: " << backupFile << endl;
    }
    
    // Ask for confirmation
    cout << "\n[WARNING] About to overwrite primary superblock!" << endl;
    cout << "          This operation will modify the device: " << devicePath << endl;
    cout << "          Do you want to continue? (yes/no): ";
    
    string response;
    cin >> response;
    
    if (response != "yes" && response != "YES" && response != "y") {
        cout << "[CANCELLED] Operation cancelled by user." << endl;
        return false;
    }
    
    // Write the backup to primary location
    cout << "\n[INFO] Writing backup superblock to primary location..." << endl;
    
    // Update the block_group_nr field to 0 for primary superblock
    bestBackup.s_block_group_nr = 0;
    
    if (!_writeSuperblock(0, bestBackup)) {
        cerr << "[ERROR] Failed to write primary superblock!" << endl;
        return false;
    }
    
    cout << "[SUCCESS] Primary superblock has been repaired!" << endl;
    
    // Update our cached copy
    primarySuperblock = bestBackup;
    
    return true;
}

bool Ext4Recovery::verifyRecovery() {
    cout << "\n[STEP 5] Verifying Recovery..." << endl;
    
    Ext4Superblock verifiedSb;
    if (!_readSuperblock(0, verifiedSb)) {
        cerr << "[ERROR] Failed to read primary superblock for verification!" << endl;
        return false;
    }
    
    _printSuperblockInfo(verifiedSb, "VERIFIED PRIMARY SUPERBLOCK");
    
    bool isValid = _verifySuperblock(verifiedSb);
    if (isValid) {
        cout << "\n[SUCCESS] Recovery verified! Primary superblock is now valid." << endl;
        cout << "          You can now try to mount the filesystem." << endl;
        return true;
    } else {
        cout << "\n[FAILURE] Verification failed! Primary superblock is still invalid." << endl;
        return false;
    }
}

void Ext4Recovery::printDeviceInfo() {
    cout << "\n========== DEVICE INFORMATION ==========" << endl;
    cout << "Device Path:       " << devicePath << endl;
    
    struct stat st;
    if (stat(devicePath.c_str(), &st) == 0) {
        cout << "Device Type:       ";
        if (S_ISBLK(st.st_mode)) {
            cout << "Block Device" << endl;
        } else if (S_ISREG(st.st_mode)) {
            cout << "Regular File (Image)" << endl;
            cout << "File Size:         " << st.st_size << " bytes ("
                 << st.st_size / (1024*1024) << " MB)" << endl;
        } else {
            cout << "Unknown" << endl;
        }
    }
    cout << "========================================" << endl;
}

void Ext4Recovery::printBackupLocations() {
    cout << "\n========== BACKUP LOCATIONS ==========" << endl;
    cout << "Standard backup superblock locations (for 4K block size):" << endl;
    for (size_t i = 0; i < backupBlockLocations.size(); i++) {
        cout << "  [" << i << "] Block " << backupBlockLocations[i] 
             << " (offset: " << backupBlockLocations[i] * BLOCK_SIZE_4K + EXT4_SUPERBLOCK_OFFSET 
             << " bytes)" << endl;
    }
    cout << "======================================" << endl;
}

bool Ext4Recovery::checkRootPermission() {
    if (geteuid() != 0) {
        cerr << "[ERROR] This program must be run with root privileges (sudo)." << endl;
        return false;
    }
    return true;
}
