#include "header.h"
#include "utils.h"

struct superBlock {//32 bytes
	BYTE superBlockSize[1];
	BYTE bytePerBlock[2];
	BYTE blocksInVolume[4];
	BYTE entryTableSize[4];
	BYTE password[16];
	BYTE unused[5];
};

struct entry { //32 bytes
	BYTE fileName[8];
	BYTE fileFormat[3];
	BYTE fileStatus[1];
	BYTE fileSize[4];
	BYTE startBlock[4];
	BYTE password[12];
};

struct dataBlock {
	BYTE data[512];
};

class Volume {
	private:
		
		bool _createBlankVolume(); // tao o dia trong
		bool _verifyVolumePassword(string password);
		bool _changeVolumePassword(string newPassword);

		bool _createSupperBlock(int volumeSize);
		bool _readSuperBlock(string volumeName);
		bool _writeSuperBlock(superBlock sb, LPCWSTR volumeName);

		// read and write entry table
		entry _createEntry(string name, string format, string password, int size, int start);
		bool _writeEntryTable(vector<entry> entryTable, LPCWSTR fileName);
		bool _readEntryTable(vector<entry>& entryTable, LPCWSTR fileName);
		entry* _searchEntry(string filename);
		bool _verifyFilePassword(string password, entry e);
		bool _changeFilePassword(entry e, string password);
		// import and export file
		int _getStartBlock();
		// Remove file
		bool _restoreableRemove(entry e, char type);
		bool _permanentRemove(entry e);

		BYTE* _readBlock(int block, LPCWSTR fileName);
		bool _writeBlock(int block, BYTE buffer[], LPCWSTR fileName);
	public:
		string volumeName;
		int volumeSize; //in MB
		vector<entry> entryTable;
		superBlock spBlock;
		string extentionTail = ".drs";
		Volume();
		~Volume();

		bool createNewVolume();
		bool readVolume();
		bool changeVolumePassword();

		void printSuperBlock(superBlock sb);
		void printEntry(entry i);
		void printEntryTable();

		bool changeFilePassword();

		bool importFile();
		bool exportFile();

		bool removeFile();

		bool restoreFile();
};