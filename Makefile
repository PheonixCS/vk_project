all: stop git_pull reqs migrate restart run

run:
# 	celery -A vk_scraping_posting worker -l info -B --detach
	celery -A vk_scraping_posting worker -l debug -B --detach
stop:
	celery multi stopwait 1 --pidfile=celeryd.pid
#     pkill -9 -f 'vk_scraping_posting worker'
restart:
	sudo systemctl restart vk_sp
git_pull:
	git pull
migrate:
	python3 manage.py migrate
reqs:
	pip3 install -r requirements.txt --no-deps
check:
	ps -aux | grep celery
