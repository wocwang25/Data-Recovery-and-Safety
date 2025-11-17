#include "ext4_recovery.h"
#include <cstdlib>

void printBanner() {
    cout << "\n";
    cout << "╔═══════════════════════════════════════════════════════════════╗\n";
    cout << "║        EXT4 FILESYSTEM RECOVERY TOOL - C++ VERSION           ║\n";
    cout << "║                                                               ║\n";
    cout << "║  Phục hồi dữ liệu Ext4 khi Superblock bị hỏng               ║\n";
    cout << "║  Recover Ext4 data when Primary Superblock is corrupted     ║\n";
    cout << "║                                                               ║\n";
    cout << "╚═══════════════════════════════════════════════════════════════╝\n";
    cout << endl;
}

void printMenu() {
    cout << "\n";
    cout << "╔═══════════════════════════════════════╗\n";
    cout << "║           MAIN MENU                   ║\n";
    cout << "╠═══════════════════════════════════════╣\n";
    cout << "║  1. Analyze Primary Superblock        ║\n";
    cout << "║  2. Scan All Backup Superblocks       ║\n";
    cout << "║  3. Find Best Backup                  ║\n";
    cout << "║  4. Repair Primary Superblock         ║\n";
    cout << "║  5. Verify Recovery                   ║\n";
    cout << "║  6. Full Auto Recovery                ║\n";
    cout << "║  7. Show Device Info                  ║\n";
    cout << "║  8. Show Backup Locations             ║\n";
    cout << "║  0. Exit                              ║\n";
    cout << "╚═══════════════════════════════════════╝\n";
    cout << endl;
}

void printUsage(const char* programName) {
    cout << "Usage: " << programName << " <device_path>" << endl;
    cout << endl;
    cout << "Examples:" << endl;
    cout << "  " << programName << " /dev/sdb1" << endl;
    cout << "  " << programName << " ext4_volume.img" << endl;
    cout << endl;
    cout << "Note: This program requires root privileges (use sudo)." << endl;
}

bool confirmDangerousOperation() {
    cout << "\n╔════════════════════════════════════════════════════════════╗\n";
    cout << "║  ⚠️  WARNING: DANGEROUS OPERATION                          ║\n";
    cout << "║                                                            ║\n";
    cout << "║  This will modify the device/image file.                  ║\n";
    cout << "║  Make sure you have a backup before proceeding!           ║\n";
    cout << "║                                                            ║\n";
    cout << "║  Type 'I UNDERSTAND' to continue: ";
    
    string response;
    getline(cin, response);
    getline(cin, response); // Clear buffer
    
    return (response == "I UNDERSTAND");
}

int main(int argc, char* argv[]) {
    // Check arguments
    if (argc != 2) {
        printUsage(argv[0]);
        return 1;
    }
    
    // Check root permission
    if (!Ext4Recovery::checkRootPermission()) {
        return 1;
    }
    
    string devicePath = argv[1];
    
    // Check if device exists
    struct stat st;
    if (stat(devicePath.c_str(), &st) != 0) {
        cerr << "[ERROR] Device or file not found: " << devicePath << endl;
        return 1;
    }
    
    printBanner();
    
    // Create recovery object
    Ext4Recovery recovery(devicePath);
    recovery.printDeviceInfo();
    
    // Main menu loop
    int choice = -1;
    bool exitProgram = false;
    
    while (!exitProgram) {
        printMenu();
        cout << "Enter your choice: ";
        cin >> choice;
        
        cout << "\n";
        
        switch (choice) {
            case 1: {
                // Analyze Primary Superblock
                recovery.analyzePrimarySuperblock();
                break;
            }
            
            case 2: {
                // Scan All Backup Superblocks
                recovery.scanBackupSuperblocks();
                break;
            }
            
            case 3: {
                // Find Best Backup
                Ext4Superblock bestBackup;
                uint64_t bestLocation;
                recovery.findBestBackup(bestBackup, bestLocation);
                break;
            }
            
            case 4: {
                // Repair Primary Superblock
                if (!confirmDangerousOperation()) {
                    cout << "[CANCELLED] Operation cancelled by user." << endl;
                    break;
                }
                recovery.repairPrimarySuperblock();
                break;
            }
            
            case 5: {
                // Verify Recovery
                recovery.verifyRecovery();
                break;
            }
            
            case 6: {
                // Full Auto Recovery
                cout << "╔═══════════════════════════════════════════════════════════════╗\n";
                cout << "║              FULL AUTOMATIC RECOVERY                          ║\n";
                cout << "╚═══════════════════════════════════════════════════════════════╝\n";
                cout << endl;
                
                if (!confirmDangerousOperation()) {
                    cout << "[CANCELLED] Operation cancelled by user." << endl;
                    break;
                }
                
                bool success = true;
                
                // Step 1: Analyze
                if (!recovery.analyzePrimarySuperblock()) {
                    cout << "\n[AUTO] Primary superblock is corrupted. Proceeding with recovery..." << endl;
                    
                    // Step 2: Scan backups
                    if (recovery.scanBackupSuperblocks()) {
                        // Step 3 & 4: Find best and repair
                        if (recovery.repairPrimarySuperblock()) {
                            // Step 5: Verify
                            if (recovery.verifyRecovery()) {
                                cout << "\n╔═══════════════════════════════════════════════════════════════╗\n";
                                cout << "║  ✅ RECOVERY COMPLETED SUCCESSFULLY!                          ║\n";
                                cout << "╚═══════════════════════════════════════════════════════════════╝\n";
                                
                                cout << "\nNext Steps:" << endl;
                                cout << "1. Run filesystem check: e2fsck -f -y " << devicePath << endl;
                                cout << "2. Try mounting (read-only): mount -o ro " << devicePath << " /mnt/recovery" << endl;
                                cout << "3. If successful, backup your data immediately!" << endl;
                            } else {
                                success = false;
                            }
                        } else {
                            success = false;
                        }
                    } else {
                        success = false;
                    }
                } else {
                    cout << "\n[AUTO] Primary superblock is valid. No recovery needed!" << endl;
                }
                
                if (!success) {
                    cout << "\n╔═══════════════════════════════════════════════════════════════╗\n";
                    cout << "║  ❌ RECOVERY FAILED                                           ║\n";
                    cout << "╚═══════════════════════════════════════════════════════════════╝\n";
                    cout << "\nPossible reasons:" << endl;
                    cout << "- All backup superblocks are also corrupted" << endl;
                    cout << "- Wrong block size assumption (not 4K)" << endl;
                    cout << "- Filesystem is not ext4 or heavily damaged" << endl;
                    cout << "\nTry using: debugfs, testdisk, or professional recovery tools." << endl;
                }
                break;
            }
            
            case 7: {
                // Show Device Info
                recovery.printDeviceInfo();
                break;
            }
            
            case 8: {
                // Show Backup Locations
                recovery.printBackupLocations();
                break;
            }
            
            case 0: {
                // Exit
                cout << "Exiting program..." << endl;
                exitProgram = true;
                break;
            }
            
            default: {
                cout << "[ERROR] Invalid choice. Please try again." << endl;
                break;
            }
        }
        
        if (!exitProgram) {
            cout << "\nPress Enter to continue...";
            cin.ignore();
            cin.get();
            cout << "\033[2J\033[1;1H"; // Clear screen
        }
    }
    
    return 0;
}
