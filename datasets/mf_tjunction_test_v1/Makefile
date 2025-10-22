# Makefile for mf_tjunction_test_v1 dataset
# Generates experiment protocols from Python generator scripts

SHELL := /bin/bash
PYTHON := python3
GENERATORS_DIR := generators
PROTOCOLS_DIR := protocols

# Find all Python generator scripts
GENERATORS := $(wildcard $(GENERATORS_DIR)/*.py)
PROTOCOLS := $(GENERATORS:$(GENERATORS_DIR)/%.py=$(PROTOCOLS_DIR)/%.txt)

.PHONY: all protocols clean help

# Default target
all: protocols

# Generate all protocols
protocols: $(PROTOCOLS_DIR) $(PROTOCOLS)
	@echo "✓ All protocols generated"

# Create protocols directory if it doesn't exist
$(PROTOCOLS_DIR):
	mkdir -p $(PROTOCOLS_DIR)

# Pattern rule: generate protocol from Python script
$(PROTOCOLS_DIR)/%.txt: $(GENERATORS_DIR)/%.py
	@echo "Generating $@..."
	cd $(GENERATORS_DIR) && $(PYTHON) $(notdir $<)

# Clean generated protocols
clean:
	rm -rf $(PROTOCOLS_DIR)
	@echo "✓ Protocols directory removed"

# Help message
help:
	@echo "Makefile for mf_tjunction_test_v1 dataset"
	@echo ""
	@echo "Targets:"
	@echo "  all (default)  - Generate all experiment protocols"
	@echo "  protocols      - Generate all experiment protocols"
	@echo "  clean          - Remove generated protocols directory"
	@echo "  help           - Show this help message"
	@echo ""
	@echo "Usage:"
	@echo "  make           - Generate all protocols"
	@echo "  make clean     - Remove all generated protocols"
	@echo ""
	@echo "Requirements:"
	@echo "  - Python 3.x"
	@echo "  - Dependencies in generators/requirements.txt"
	@echo ""
	@echo "Generated protocols will be saved to: $(PROTOCOLS_DIR)/"

