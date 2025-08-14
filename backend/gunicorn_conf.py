import os

bind = "0.0.0.0:" + os.getenv("PORT", "8080")
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("THREADS", "2"))
worker_class = "gthread"
timeout = int(os.getenv("TIMEOUT", "120"))
keepalive = 10
accesslog = "-"
errorlog = "-"
