FROM redis:7.2-alpine

# Copy custom Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf

# Create data directory
RUN mkdir -p /data

# Expose Redis port
EXPOSE 6379

# Start Redis with custom config
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]
