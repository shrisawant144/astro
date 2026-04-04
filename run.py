"""
Vedic Kundali - Entry point
Run: python run.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kundali_gui import KundaliApp

if __name__ == "__main__":
    app = KundaliApp()
    app.mainloop()
