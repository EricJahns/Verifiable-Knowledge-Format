.PHONY: install lint type test validate strict okf graph all

install:
	pip install -e ".[dev]" types-PyYAML

lint:
	ruff check src tests

type:
	mypy src/vkf

test:
	pytest --cov=vkf --cov-report=term-missing

validate:
	vkf validate examples

strict:
	vkf validate examples --profile 2 --verbose

okf:
	vkf to-okf examples --out okf-export && vkf import-okf okf-export && vkf validate okf-export --profile 0

graph:
	vkf graph examples --out graph.json

all: lint type test validate okf
