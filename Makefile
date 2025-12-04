# IPI-Shield Makefile
# Enterprise-grade build automation

.PHONY: help install install-dev install-all lint format type-check test test-cov clean run docs docker

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)IPI-Shield$(NC) - Indirect Prompt Injection Defence Layer"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Installation
# =============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	pip install --upgrade pip
	pip install -e .

install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install

install-all: ## Install all dependencies (including ML and OCR)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	pip install --upgrade pip
	pip install -e ".[all]"
	pre-commit install

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run linting checks
	@echo "$(BLUE)Running flake8...$(NC)"
	flake8 backend tests --max-line-length=100 --ignore=E501,W503
	@echo "$(GREEN)✓ Linting passed$(NC)"

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	isort backend tests
	black backend tests
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check formatting without making changes
	@echo "$(BLUE)Checking code format...$(NC)"
	isort --check-only backend tests
	black --check backend tests

type-check: ## Run mypy type checking
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy backend --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking passed$(NC)"

quality: lint type-check ## Run all quality checks
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=backend --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

test-fast: ## Run tests without slow markers
	@echo "$(BLUE)Running fast tests...$(NC)"
	pytest tests/ -v -m "not slow"

# =============================================================================
# Development Server
# =============================================================================

run: ## Run development server
	@echo "$(BLUE)Starting IPI-Shield server...$(NC)"
	@echo "$(GREEN)Dashboard: http://127.0.0.1:8000/dashboard$(NC)"
	@echo "$(GREEN)API Docs:  http://127.0.0.1:8000/docs$(NC)"
	python run.py --reload

run-prod: ## Run production server
	@echo "$(BLUE)Starting production server...$(NC)"
	uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "Documentation available at /docs endpoint"

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t ipi-shield:latest .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 8000:8000 ipi-shield:latest

docker-compose-up: ## Start with Docker Compose
	docker-compose up -d

docker-compose-down: ## Stop Docker Compose
	docker-compose down

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

clean-all: clean ## Clean everything including venv
	rm -rf venv/
	rm -rf .venv/

# =============================================================================
# Security
# =============================================================================

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	pip-audit
	bandit -r backend/ -ll

# =============================================================================
# Release
# =============================================================================

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	python -m build
	@echo "$(GREEN)✓ Build complete$(NC)"

publish-test: build ## Publish to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	twine upload dist/*
