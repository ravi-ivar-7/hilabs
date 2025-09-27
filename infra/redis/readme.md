# Redis Setup

## Start Redis Service
```bash
docker-compose up redis
```

## Access Redis CLI
```bash
docker exec -it hilabs-redis redis-cli
```

## Configuration
- **Port**: 6379
- **Memory Limit**: 512MB
- **Databases**: 16 (for Celery task separation)
- **Persistence**: Disabled for development performance

## Celery Integration
- **Broker URL**: `redis://redis:6379/0`
- **Result Backend**: `redis://redis:6379/1`
- **Task Database**: Database 0
- **Results Database**: Database 1
