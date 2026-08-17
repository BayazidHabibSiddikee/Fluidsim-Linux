#!/usr/bin/env python3
"""FluidSim Linux - Hydraulic & Pneumatic Circuit Simulator"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.app import main
if __name__ == "__main__":
    main()
