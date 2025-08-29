# YOLOv11e PII Detection Pipeline - Makefile
# Provides convenient commands for development and usage

.PHONY: help install test clean examples run-cli setup-dirs

# Default target
help:
	@echo "🚀 YOLOv11e PII Detection Pipeline"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run unit tests"
	@echo "  examples     - Run example scripts"
	@echo "  clean        - Clean up generated files"
	@echo "  setup-dirs   - Create sample directories"
	@echo "  run-cli      - Show CLI help"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code with black"
	@echo ""

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully!"

# Install development dependencies
install-dev: install
	@echo "🔧 Installing development dependencies..."
	pip install -e .
	@echo "✅ Development dependencies installed!"

# Run unit tests
test:
	@echo "🧪 Running unit tests..."
	python -m pytest tests/ -v
	@echo "✅ Tests completed!"

# Run examples
examples:
	@echo "📚 Running example scripts..."
	@echo ""
	@echo "Basic usage examples:"
	python examples/basic_usage.py
	@echo ""
	@echo "Custom classes examples:"
	python examples/custom_classes.py
	@echo ""
	@echo "Batch processing examples:"
	python examples/batch_processing.py
	@echo "✅ Examples completed!"

# Clean up generated files
clean:
	@echo "🧹 Cleaning up generated files..."
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf output_images/
	rm -rf output_videos/
	@echo "✅ Cleanup completed!"

# Create sample directories
setup-dirs:
	@echo "📁 Setting up sample directories..."
	mkdir -p sample_images/identity_docs
	mkdir -p sample_images/financial_docs
	mkdir -p sample_images/medical_docs
	mkdir -p sample_images/digital_screens
	mkdir -p sample_videos/meetings
	mkdir -p sample_videos/presentations
	mkdir -p output_images
	mkdir -p output_videos
	@echo "✅ Sample directories created!"
	@echo ""
	@echo "💡 Add your test images/videos to the sample directories:"
	@echo "   - sample_images/ - for .jpg, .jpeg, .png files"
	@echo "   - sample_videos/ - for .mp4, .avi, .mov files"

# Show CLI help
run-cli:
	@echo "🖥️  Command Line Interface Help"
	@echo "================================"
	python cli.py --help

# Run code linting
lint:
	@echo "🔍 Running code linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 pii_detector.py examples/ tests/ cli.py; \
	else \
		echo "⚠️  flake8 not found. Install with: pip install flake8"; \
	fi
	@if command -v mypy >/dev/null 2>&1; then \
		mypy pii_detector.py examples/ tests/ cli.py; \
	else \
		echo "⚠️  mypy not found. Install with: pip install mypy"; \
	fi
	@echo "✅ Linting completed!"

# Format code with black
format:
	@echo "🎨 Formatting code with black..."
	@if command -v black >/dev/null 2>&1; then \
		black pii_detector.py examples/ tests/ cli.py; \
		echo "✅ Code formatting completed!"; \
	else \
		echo "⚠️  black not found. Install with: pip install black"; \
	fi

# Quick start - setup everything needed to get started
quickstart: setup-dirs install
	@echo ""
	@echo "🎉 Quick start setup completed!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Add test images to sample_images/ directory"
	@echo "2. Add test videos to sample_videos/ directory"
	@echo "3. Run examples: make examples"
	@echo "4. Test CLI: make run-cli"
	@echo "5. Process files: python cli.py image input.jpg output.jpg"

# Development workflow
dev: install-dev lint test
	@echo "✅ Development workflow completed!"

# Show project status
status:
	@echo "📊 Project Status"
	@echo "================="
	@echo "Python version: $(shell python --version)"
	@echo "Dependencies: $(shell pip list | grep -E "(ultralytics|opencv|numpy)" | wc -l) installed"
	@echo "Sample directories: $(shell find sample_* -type d 2>/dev/null | wc -l) created"
	@echo "Output directories: $(shell find output_* -type d 2>/dev/null | wc -l) created"
	@echo ""
	@echo "Files in project:"
	@find . -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.json" | head -20
