project/
│── docker-compose.yml        # Orchestration for frontend, backend, workers, broker, flower, infra
│── .env                      # Environment variables (shared configs)
│── .env.example                # Environment variables examples
│── README.md                 # Documentation
│
├── frontend/                 # Next.js app (app based routers)
│   ├── package.json
│   ├── next.config.js
│   ├── public/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── lib/
│
├── backend/                  # FastAPI app
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint
│   │   ├── api/              # Route definitions
│   │   ├── core/             # Configs, logging, settings
│   │   ├── services/         # Contract analysis business logic
│   │   ├── data/             # Contract files and templates
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic models
│   │   ├── utils/            # Utility functions
│
├── worker/                   # Celery worker with tasks
│   ├── tasks/                # Task definitions here
│   ├── requirements.txt
│   └── worker.py
│
├── flower/                   # Flower dashboard
│   ├── Dockerfile
│   └── config.py             # Optional Flower configs
│
└── infra/                    # Infrastructure configs
    ├── redis/             # Redis config (plugins, definitions.json)
    └── minio/               # MinIO configuration
└── docs/                     # Additional documentation
    ├── api.md                # API documentation
    └── deployment.md         # Deployment guide