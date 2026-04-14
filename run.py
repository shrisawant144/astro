"""
Vedic Kundali - Entry point
Run: python run.py
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from kundali.main import main

if __name__ == "__main__":
    main()
