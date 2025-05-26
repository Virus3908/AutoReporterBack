.PHONY: run
run: generate
	python -m app.main

.PHONY: generate
generate:
	python -m grpc_tools.protoc -I=proto --python_out=app/generated proto/messages.proto

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +

.PHONY: lint
lint:
	flake8 app

.PHONY: format
format:
	black app
	isort app

.PHONY: freeze
freeze:
	pip freeze > requirements.txt
