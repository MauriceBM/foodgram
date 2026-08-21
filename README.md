# Foodgram

Foodgram — социальная сеть для обмена рецептами. Пользователи могут публиковать рецепты, подписываться на других авторов, добавлять рецепты в избранное и формировать список покупок.

## Технологии

- Python 3.12
- Django 4.2
- Django REST Framework 3.14
- Djoser (аутентификация)
- PostgreSQL 16
- Docker / Docker Compose
- Nginx
- React (frontend)

## Локальный запуск

1. Клонируйте репозиторий:
   ```bash
   git clone <URL> && cd foodgram
   ```

## Создайние файл окружения

cp backend/.env.example backend/.env

## Запуст контейнеры

docker compose up --build -d

## Примениние миграции и собрание статику

docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput

## Импорт ингредиенты

docker compose exec backend python manage.py load_ingredients /app/data/ingredients.json

## Создание суперпользователя

docker compose exec -it backend python manage.py createsuperuser

По адресу http://localhost изучите фронтенд веб-приложения, а по адресу http://localhost/api/docs/ — спецификацию API.
