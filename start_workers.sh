sudo service redis-server start
dramatiq --threads 1 vapour.workers --watch .
