.PHONY: test build

test: build
		python -m pytest tests/

build:
		python setup.py install

clean:
	rm -rf *egg-info .eggs dist build

# TODO for later:
# automate building system using CI (via github)
# Build static files
