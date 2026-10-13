.PHONY: install test validate benchmark

install:
	python -m pip install -r requirements-dev.txt

test:
	python -m pytest -q

validate:
	python -m py_compile src/*.py
	python -m pytest -q

# Full end-to-end QAOA run; can take several minutes due to the multi-seed simulations.
benchmark:
	python -m nbconvert --to notebook --execute --inplace main.ipynb --ExecutePreprocessor.timeout=2400
