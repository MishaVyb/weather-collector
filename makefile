migrations:
	docker-compose exec worker alembic upgrade head

initialization:
	docker-compose exec worker python manage.py fetch_cities

collecting:
	docker-compose exec worker python manage.py collect

start:
	docker-compose build
	docker-compose up -d
	make migrations
	make initialization
	make collecting

