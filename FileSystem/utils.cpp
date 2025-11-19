#include "utils.h"

BYTE* decToHexaLE(unsigned int num, int size) {
	BYTE* byte = createBlankOffsets(size);
	int index = 0;

	while (num > 0 && index < size) {
		byte[index] = BYTE(num & 0xFF);
		num = num >> 8;
		index++;
	}

	return byte;
}
BYTE* createBlankOffsets(int n) {
	BYTE* offsets = new BYTE[n];

	for (int i = 0; i < n; i++) {
		offsets[i] = BYTE(0);
	}
	return offsets;
}

BYTE hexToByte(const string& hexString) {
	if (hexString.size() != 2) {
		// Handle invalid input
		throw invalid_argument("Input must be a two-character hexadecimal string");
	}
	try {
		// Convert the hexadecimal string to an integer
		int hexValue = stoi(hexString, 0, 16);

		// Convert the integer to an unsigned char
		unsigned char result = static_cast<unsigned char>(hexValue);

		return result;
	}
	catch (const out_of_range& e) {
		// Handle out-of-range error
		throw out_of_range("Hexadecimal value out of range for unsigned char");
	}
	catch (const invalid_argument& e) {
		// Handle invalid argument error
		throw invalid_argument("Invalid hexadecimal string");
	}
}

string byteToHex(unsigned char byte) {
	std::ostringstream oss;
	oss << setw(2) << setfill('0') << hex << static_cast<int>(byte);
	return oss.str();
}
int reverseByte(BYTE* byte, unsigned int count)
{
	int result = 0;
	for (int i = count - 1; i >= 0; i--)
		result = (result << 8) | byte[i];
	return result;
}

bool isBufferEmpty(const BYTE* buffer, size_t size) {
	// Check if the buffer is null
	if (buffer == nullptr) {
		return true;
	}

	// Check if all bytes in the buffer are 0
	for (size_t i = 0; i < size; ++i) {
		if (buffer[i] != BYTE(0)) {
			return false;
		}
	}

	return true;
}

bool isEntryEmpty(int index, BYTE* buffer) {
	for (size_t i = index; i < index + 32; ++i) {
		if (buffer[i] != BYTE(0)) {
			return false;
		}
	}
	return true;
}
BYTE* createBlankOffets(int n) {
	BYTE* offsets = new BYTE[n];

	for (int i = 0; i < n; i++) {
		offsets[i] = BYTE(0);
	}
	return offsets;
}