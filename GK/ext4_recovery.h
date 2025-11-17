#pragma once

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstring>
#include <iomanip>
#include <sstream>
#include <fcntl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <cstdint>

#define EXT4_SUPERBLOCK_OFFSET 1024
#define EXT4_SUPERBLOCK_SIZE 1024
#define EXT4_MAGIC 0xEF53
#define BLOCK_SIZE_4K 4096

using namespace std;

// Cấu trúc Ext4 Superblock (đơn giản hóa - các trường quan trọng)
struct Ext4Superblock {
    uint32_t s_inodes_count;           // 0: Tổng số inodes
    uint32_t s_blocks_count_lo;        // 4: Tổng số blocks (low 32 bits)
    uint32_t s_r_blocks_count_lo;      // 8: Reserved blocks (low 32 bits)
    uint32_t s_free_blocks_count_lo;   // 12: Free blocks (low 32 bits)
    uint32_t s_free_inodes_count;      // 16: Free inodes
    uint32_t s_first_data_block;       // 20: First data block
    uint32_t s_log_block_size;         // 24: Block size = 1024 << s_log_block_size
    uint32_t s_log_cluster_size;       // 28: Cluster size
    uint32_t s_blocks_per_group;       // 32: Blocks per group
    uint32_t s_clusters_per_group;     // 36: Clusters per group
    uint32_t s_inodes_per_group;       // 40: Inodes per group
    uint32_t s_mtime;                  // 44: Mount time
    uint32_t s_wtime;                  // 48: Write time
    uint16_t s_mnt_count;              // 52: Mount count
    uint16_t s_max_mnt_count;          // 54: Max mount count
    uint16_t s_magic;                  // 56: Magic signature (0xEF53)
    uint16_t s_state;                  // 58: File system state
    uint16_t s_errors;                 // 60: Behaviour when detecting errors
    uint16_t s_minor_rev_level;        // 62: Minor revision level
    uint32_t s_lastcheck;              // 64: Time of last check
    uint32_t s_checkinterval;          // 68: Max time between checks
    uint32_t s_creator_os;             // 72: OS
    uint32_t s_rev_level;              // 76: Revision level
    uint16_t s_def_resuid;             // 80: Default uid for reserved blocks
    uint16_t s_def_resgid;             // 82: Default gid for reserved blocks
    
    // Extended fields
    uint32_t s_first_ino;              // 84: First non-reserved inode
    uint16_t s_inode_size;             // 88: Size of inode structure
    uint16_t s_block_group_nr;         // 90: Block group # of this superblock
    uint32_t s_feature_compat;         // 92: Compatible feature set
    uint32_t s_feature_incompat;       // 96: Incompatible feature set
    uint32_t s_feature_ro_compat;      // 100: Readonly-compatible feature set
    uint8_t  s_uuid[16];               // 104: 128-bit UUID for volume
    char     s_volume_name[16];        // 120: Volume name
    
    // ... có thể thêm các trường khác nếu cần
    uint8_t  padding[EXT4_SUPERBLOCK_SIZE - 136]; // Padding to 1024 bytes
};

// Class chính để phục hồi Ext4
class Ext4Recovery {
private:
    string devicePath;
    int deviceFd;
    Ext4Superblock primarySuperblock;
    vector<uint64_t> backupBlockLocations;
    bool deviceOpened;
    
    // Private methods
    bool _openDevice();
    void _closeDevice();
    bool _readSuperblock(uint64_t blockNumber, Ext4Superblock& sb);
    bool _writeSuperblock(uint64_t blockNumber, const Ext4Superblock& sb);
    bool _verifySuperblock(const Ext4Superblock& sb);
    void _calculateBackupLocations(uint32_t blockSize);
    uint32_t _getBlockSize(const Ext4Superblock& sb);
    bool _compareSuperblocks(const Ext4Superblock& sb1, const Ext4Superblock& sb2);
    void _printSuperblockInfo(const Ext4Superblock& sb, const string& label);
    
public:
    Ext4Recovery(const string& device);
    ~Ext4Recovery();
    
    // Public methods
    bool analyzePrimarySuperblock();
    bool scanBackupSuperblocks();
    bool findBestBackup(Ext4Superblock& bestBackup, uint64_t& bestBlockLocation);
    bool repairPrimarySuperblock();
    bool verifyRecovery();
    
    // Utility methods
    void printDeviceInfo();
    void printBackupLocations();
    static bool checkRootPermission();
};

// Utility functions
namespace Ext4Utils {
    string bytesToHex(const uint8_t* bytes, size_t length);
    string formatBlockSize(uint32_t blockSize);
    string formatTimestamp(uint32_t timestamp);
    bool isValidMagic(uint16_t magic);
    uint64_t calculateBlockOffset(uint64_t blockNumber, uint32_t blockSize);
}
