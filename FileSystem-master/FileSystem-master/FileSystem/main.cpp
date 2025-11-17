#include "header.h"
#include "volume.h"

int main() {

	Volume myFS;
	bool btn2 = 0;
	int btn1 = 0;
	// mo hoac tao volume
	do {
		do {
			cout << "-----FILE SYSTEM-----" << endl;
			cout << "Enter 1: Create new volume" << endl;
			cout << "Enter 2: Open existed volume" << endl;
			cout << "Enter your choice: ";
			cin >> btn1;
		} while (btn1 != 1 && btn1 != 2);

		if (btn1 == 1) {
			// create new volume
			btn2 = myFS.createNewVolume();
		}
		else {
			// open existed volume
			btn2 = myFS.readVolume();
		}
		system("pause");
		system("cls");
	} while (!btn2);

	do {
		cout << "-----" << myFS.volumeName << ".drs-----" << endl;
		cout << "Enter 1: Change volume password" << endl;
		cout << "Enter 2: Show files list" << endl;
		cout << "Enter 3: Modify file password" << endl;
		cout << "Enter 4: Import file" << endl;
		cout << "Enter 5: Export file" << endl;
		cout << "Enter 6: Remove file" << endl;
		cout << "Enter 7: Restore file" << endl;
		cout << "Enter 0: Exit" << endl;
		cout << "Enter your choice: ";
		cin >> btn1;

		switch (btn1) {
		case 1:
			myFS.changeVolumePassword();
			break;
		case 2:
			myFS.printEntryTable();
			break;
		case 3:
			myFS.changeFilePassword();
			break; 
		case 4:
			myFS.importFile();
			break; 
		case 5:
			myFS.exportFile();
			break; 
		case 6:
			myFS.removeFile();
			break;
		case 7:
			myFS.restoreFile();
			break;
		default:
			break;
		}
		system("pause");
		system("cls");
	} while (btn1);
	// cac tinh nang truy xuat khac


	system("pause");
	return 0;
}