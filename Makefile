SHELL = /bin/bash

.ONESHELL:

LUNA_HOME ?= ${PWD}
export LUNA_HOME

VENV_PATH = .venv
VENV = ${VENV_PATH}/luna

# NB: this conda activation only works if the environment is not activated
CONDA_ACTIVATE = source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate

DOCKER_NAME := mskmind/luna
DOCKER_TAG := $$(git log -1 --pretty=%h)
DOCKER_BUILD_OPTS = --build-arg YOUR_ENV=dev

.DEFAULT_GOAL := help


help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

clean: clean-test ## remove all artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	conda env remove --prefix $(VENV)
.PHONY: clean

clean-test: ## remove test and coverage artifacts
	rm -fr .pytest_cache
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
.PHONY: clean-test

venv: ## create conda environment and install luna
	mamba env update --prefix $(VENV) --prune -f environment.yml
	$(CONDA_ACTIVATE) $(VENV)
	SETUPTOOLS_USE_DISTUTILS=stdlib poetry install
.PHONY: venv

build: ## build python package
	$(CONDA_ACTIVATE) $(VENV)
	poetry build
.PHONY: build

build-docker: ## build production docker image
	docker build ${DOCKER_BUILD_OPTS} --tag ${DOCKER_NAME}:${DOCKER_TAG} .
	docker tag ${DOCKER_NAME}:${DOCKER_TAG} ${DOCKER_NAME}:latest
.PHONY: build-docker


#test-upload:
#	python3 -m twine upload --verbose --repository testpypi dist/*.whl

#upload:
#	python3 -m twine upload dist/*.whl

# https://python-semantic-release.readthedocs.io/en/latest/#semantic-release-publish
# Same command can be executed in the subpackage directory for testing purposes.
# For releases, this will be automated with github actions, and these commands in the makefile are for testing purposes only.
# This will change your branch to the master branch.
test-upload-pypi: ## dry run of upload wheel to testpypi.
	$(CONDA_ACTIVATE) $(VENV)
	semantic-release publish --noop -v DEBUG -D upload_to_pypi=True -D repository=pypitest -D upload_to_release=False
.PHONY: test-upload

upload-pypi: ## upload wheel to pypi and publish to github
	$(CONDA_ACTIVATE) $(VENV)
	semantic-release publish  -v DEBUG -D upload_to_pypi=True -D repository=pypi -D upload_to_release=True
.PHONY: upload-pypi

.PHONY: blackstyle
blackstyle: ## check code style with black
	$(CONDA_ACTIVATE) $(VENV)
	black --diff src tests

.PHONY: flake8style
flake8style: ## check flake8 convertions with flake8
	$(CONDA_ACTIVATE) $(VENV)
	flake8 src

.PHONY: pydocstyle
pydocstyle: ## check docstring formatting
	$(CONDA_ACTIVATE) $(VENV)
	pydocstyle --convention=numpy src/

isort: ## run isort to sort imports
	$(CONDA_ACTIVATE) $(VENV)
	isort --profile black --filter-files src tests
.PHONY: isort

test: clean-test   ## run tests quickly with the default Python
	$(CONDA_ACTIVATE) $(VENV)
	pytest
.PHONY: test

coverage: ## pytest test coverage
	$(CONDA_ACTIVATE) $(VENV)
	pytest -s --cov=src .
	coverage report -m
	coverage html
	open htmlcov/index.html
.PHONY: coverage

build-docs: ## mkdocs build
	$(CONDA_ACTIVATE) $(VENV)
	mkdocs build

serve-docs: ## serve docs locally
	$(CONDA_ACTIVATE) $(VENV)
	mkdocs serve --dirtyreload -a 0.0.0.0:8000

deploy-docs: ## deploy docs
	$(CONDA_ACTIVATE) $(VENV)
	mkdocs gh-deploy
