all: stop reqs migrate restart run

run:
#	celery -A vk_scraping_posting worker -l info -B --detach
	celery -A vk_scraping_posting worker -l debug -B --detach
#	python moderation/tasks/send_message_to_comment.py
stop:
	celery multi stopwait 1 --pidfile=celeryd.pid
#     pkill -9 -f 'vk_scraping_posting worker'
restart:
	sudo systemctl restart vk_sp
migrate:
	python3 manage.py migrate
reqs:
	pip3 install -r requirements.txt --no-deps
check:
	ps -aux | grep celery
