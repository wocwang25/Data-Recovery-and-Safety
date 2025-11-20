import os
import sys


def check_root():
    """Kiểm tra quyền root"""
    if os.geteuid() != 0:
        print("This program requires root privileges!")
        print("Please run with: sudo python3 main.py <image_file>")
        sys.exit(1)


def print_menu():
    """In menu options"""
    print("\n" + "=" * 70)
    print("EXT4 FILE CARVING - MENU")
    print("=" * 70)
    print("1. Check data (kiểm tra filesystem và files)")
    print("2. Delete data (xóa files/folders để test)")
    print("3. Recover data (phục hồi files + directories)")
    print("0. Exit")
    print("=" * 70)


def get_menu_choice():
    """Lấy user choice"""
    try:
        choice = input("\nSelect option [0-3]: ").strip()
        return choice
    except (EOFError, KeyboardInterrupt):
        print("\n\nExiting...")
        sys.exit(0)
