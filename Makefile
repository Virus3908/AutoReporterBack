HOST = localhost
PORT = 8081

run:
	python -m app.main

generate:
	python -m grpc_tools.protoc -I=proto --python_out=app/generated proto/messages.proto

test:
	pytest tests/