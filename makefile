# This file presents CLI shortcuts.
# Go there to find more details: https://makefiletutorial.com/#variables

migrations:
	docker-compose exec worker alembic upgrade head

initialization:
	docker-compose exec worker python manage.py fetch_cities

collecting:
	docker-compose exec worker python manage.py collect

app:
	docker-compose build
	docker-compose up -d
	make migrations
	make initialization
	make collecting


######################################################################
# development tools
######################################################################


format:
	@autoflake --remove-all-unused-imports -vv --ignore-init-module-imports -r .
	@echo "make format is calling for autoflake, which  will remove all unused imports listed above. Are you sure?"
	@echo "Enter to proceed. Ctr-C to abort."
	@read
	autoflake --in-place --remove-all-unused-imports  --ignore-init-module-imports -r .
	black .
	isort .
	mypy .
	flake8 .


push:
	make format
	@git status
	@echo "All files listed above will be added to commit. Enter commit message to proceed. Ctr-C to abort."
	@read -p "Commit message: " COMMIT_MESSAGE; git add . ; git commit -m "$$COMMIT_MESSAGE"
	@git push

