install: ## Install all dependencies
	uv sync && npm install

install-py: ## Install Python dependencies
	uv sync

up: up-flask-local  ## Run Flask locally

up-flask-local: ## Stands up flask
	uv run flask --app standup_report/app.py --debug run --port 2300

# TODO: might want to also support docker... maybe...

upgrade-py:
	uv lock --upgrade

lint: ## Lint and format all code
	uv run ruff check --fix .; uv run black . ; uv run mypy . ; npm run format
