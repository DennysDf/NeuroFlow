.PHONY: install run migrate revision seed test lint format tw-build tw-watch

install:
	pip install -r requirements.txt
	npm install

run:
	flask run --debug

migrate:
	flask db upgrade

revision:
	flask db migrate -m "$(m)"

seed:
	python scripts/seed.py

test:
	pytest -q

lint:
	ruff check app tests scripts

format:
	black app tests scripts
	ruff check --fix app tests scripts

tw-build:
	npm run build

tw-watch:
	npm run dev
