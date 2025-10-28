.PHONY: setup clean run build start stop logs

setup:
	mkdir -p app
	mkdir -p config
	mkdir -p logs
	mkdir -p tests
	touch app/__init__.py
	touch app/main.py
	touch app/bot.py
	touch app/bybit_client.py
	touch app/webhook_handler.py
	touch app/order_manager.py
	touch config/config.json
	touch config/testnet.json
	touch config/prod.json
	touch requirements.txt
	touch .env.dev
	touch .gitignore
	touch README.md
	touch docker-compose.yml
	touch Dockerfile

clean:
	rm -rf app
	rm -rf config
	rm -rf logs
	rm -rf tests
	rm -f requirements.txt
	rm -f .gitignore
	rm -f README.md
	rm -f docker-compose.yml
	rm -f Dockerfile

run:
	python app/main.py

build:
	docker-compose build

start:
	docker-compose up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f tradebot