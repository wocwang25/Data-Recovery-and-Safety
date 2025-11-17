#include "header.h"

BYTE* decToHexaLE(unsigned int num, int n);
BYTE* createBlankOffsets(int n);
BYTE hexToByte(const string& hexString);
string byteToHex(unsigned char byte);
int reverseByte(BYTE* byte, unsigned int count);
bool isBufferEmpty(const BYTE* buffer, size_t size);
bool isEntryEmpty(int index, BYTE* buffer);
BYTE* createBlankOffets(int n);