.PHONY: build test

build:
	docker-compose up -d --build
test:
	@echo "Running tests..."
	docker-compose run app python -m unittest tests/tests.py
