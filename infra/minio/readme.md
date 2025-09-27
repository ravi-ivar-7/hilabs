# MinIO Setup

## Start MinIO Service
```bash
docker-compose up minio
```

## Initialize Buckets
```bash
docker exec -it hilabs-minio /usr/local/bin/init-buckets.sh
```

## Access MinIO
- **Console**: http://localhost:9001
- **API**: http://localhost:9000
- **Credentials**: hilabs / hilabsminio (as defined in .env file)

## Buckets Created
- `contracts-tn` - Tennessee healthcare contracts
- `contracts-wa` - Washington healthcare contracts  
- `templates` - Standard contract templates
- `processed` - Classification results
