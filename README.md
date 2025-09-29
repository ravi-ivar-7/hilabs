**Github Link:** https://github.com/ravi-ivar-7/hilabs

# HiLabs Hackathon 2025: Healthcare Contract Language Classification

## Author
- **Name:** Ravi Kumar
- **GitHub:** [@ravi-ivar-7](https://github.com/ravi-ivar-7)
- **Institution:** IIT Kharagpur
- **Team:** retrostoat

## Development Environment
- **OS**: Linux 6.14.0-29-generic #29~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC x86_64
- **CPU**: 12th Gen Intel(R) Core(TM) i5-1240P
- **RAM**: 7.4Gi total
- **Node.js**: v20.16.0
- **Python**: 3.12.3
- **Docker**: 28.4.0


## Quick Setup

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)
- 8GB+ RAM recommended

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ravi-ivar-7/hilabs.git
   cd hilabs
   ```

2. **Choose your setup method:**

#### Option A: Docker Setup (Recommended)
```bash
docker-compose up --build
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

**Note**: Docker may take some time to build and start all services (backend, frontend, worker, Redis). Please be patient during the initial setup. 😊

#### Option B: Local Development Setup
```bash
# Copy environment configuration
cp .env.example .env

# Start all services locally
./services.sh start
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Redis**: localhost:6379

