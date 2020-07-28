.PHONY: test
.PHONY: lint

test:
	python -m unittest -v

lint:
	python -m mypy --ignore-missing-imports --scripts-are-modules --follow-imports=skip notify
