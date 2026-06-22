# ====================================================================
# 🗂️ CARTA EDGE-CLOUD INTEGRATED PROJECT MAKEFILE
# ====================================================================
# This Makefile (mf file) coordinates building, configuring, and 
# launching the Cart Edge and Cloud elements.
# ====================================================================

.PHONY: help setup run-car run-cloud clean

default: help

help:
	@echo "===================================================================="
	@echo "🚀 CARTA 001 - MULTI-NODE AWS IOT AUTOMATION MANAGER"
	@echo "===================================================================="
	@echo "Available Targets:"
	@echo "  make setup       - Install Python dependencies (Flask, paho-mqtt, pyserial, smbus2)"
	@echo "  make run-car     - Start the Cart 001 Edge telemetry & command loop"
	@echo "  make run-cloud   - Boot the real-time Flask Web Command Dashboard"
	@echo "  make clean       - Clean temporary Cache files (.pyc, __pycache__)"
	@echo "===================================================================="

setup:
	@echo "⏳ Checking and installing python mechatronic & server dependencies..."
	pip3 install Flask paho-mqtt pyserial smbus2
	@echo "✅ Setup complete! Make sure you are in the dialout group if running on Raspberry Pi:"
	@echo "   sudo usermod -a -G dialout \$$USER"

run-car:
	@echo "🔋 Starting Cart 001 physical sensors edge node..."
	cd car && python3 carta_edge.py

run-cloud:
	@echo "☁️ Launching AWS Tele-Operation Command Dashboard..."
	cd cloud && python3 cloud_dashboard.py

clean:
	@echo "🧹 Cleaning temporary Python Cache artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✨ Clean complete."
