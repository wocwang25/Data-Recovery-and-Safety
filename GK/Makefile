# Makefile for Ext4 Recovery Tool
# Compiler: g++

CXX = g++
CXXFLAGS = -std=c++11 -Wall -Wextra -O2
TARGET = ext4_recovery
SOURCES = main_ext4_recovery.cpp ext4_recovery.cpp
OBJECTS = $(SOURCES:.cpp=.o)
HEADERS = ext4_recovery.h

# Default target
all: $(TARGET)

# Link object files to create executable
$(TARGET): $(OBJECTS)
	@echo "Linking..."
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(OBJECTS)
	@echo "Build successful! Executable: $(TARGET)"
	@echo ""
	@echo "Usage: sudo ./$(TARGET) <device_path>"

# Compile source files to object files
%.o: %.cpp $(HEADERS)
	@echo "Compiling $<..."
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(OBJECTS) $(TARGET)
	@echo "Clean complete."

# Install (optional - copy to /usr/local/bin)
install: $(TARGET)
	@echo "Installing to /usr/local/bin..."
	sudo cp $(TARGET) /usr/local/bin/
	@echo "Installation complete. You can now run: sudo $(TARGET) <device>"

# Uninstall
uninstall:
	@echo "Uninstalling from /usr/local/bin..."
	sudo rm -f /usr/local/bin/$(TARGET)
	@echo "Uninstallation complete."

# Help
help:
	@echo "Ext4 Recovery Tool - Makefile Commands"
	@echo ""
	@echo "Available targets:"
	@echo "  make           - Build the project (default)"
	@echo "  make clean     - Remove build artifacts"
	@echo "  make install   - Install to /usr/local/bin"
	@echo "  make uninstall - Remove from /usr/local/bin"
	@echo "  make help      - Show this help message"
	@echo ""
	@echo "Usage after building:"
	@echo "  sudo ./ext4_recovery /dev/sdX"
	@echo "  sudo ./ext4_recovery volume.img"

# Phony targets (not actual files)
.PHONY: all clean install uninstall help
