max_threads = Integer(ENV.fetch("RAILS_MAX_THREADS", 5))
min_threads = Integer(ENV.fetch("RAILS_MIN_THREADS", max_threads))
threads min_threads, max_threads

environment ENV.fetch("RAILS_ENV", "development")

bind "tcp://0.0.0.0:#{ENV.fetch('PORT', 8080)}"
