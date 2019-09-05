all: stop git_pull reqs migrate restart run

run:
	celery -A vk_scraping_posting worker --concurrency=4 -l info -B --detach
stop:
	celery multi stop 1 --pidfile=celeryd.pid
restart:
	sudo systemctl restart vk_sp
git_pull:
	git pull
migrate:
	python3 manage.py migrate
reqs:
	pip3 install -r requirements.txt
check:
	ps -aux | grep celery
