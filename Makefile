HOST = localhost
PORT = 8081

run:
	uvicorn app.main:app --host $(HOST) --port=$(PORT)

prod:
	uvicorn app.main:app --host 0.0.0.0 --port=8080 --workers=4

test:
	pytest tests/