.PHONY: install migrate run test compose-up compose-down backup
install:
	python3 -m pip install --user --break-system-packages -e '.[postgres,test]'
migrate:
	alembic upgrade head
run:
	uvicorn apps.diagnostic_api.main:app --reload --port 8000
test:
	python3 -m pytest
compose-up:
	docker compose up --build -d
compose-down:
	docker compose down
backup:
	./deployment/on_prem/backup.sh

