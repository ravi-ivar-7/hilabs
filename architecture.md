# Healthcare Contract Classification System Architecture

## System Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │    Backend      │    │     Worker      │    │  Classification │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Celery)      │◄──►│    Engine       │
│                 │    │                 │    │                 │    │   (spaCy+SBERT) │
│ • Upload UI     │    │ • REST API      │    │ • Async Tasks   │    │ • NLP Models    │
│ • Dashboard     │    │ • Database      │    │ • Redis Queue   │    │ • Templates     │
│ • Results       │    │ • File Storage  │    │ • Processing    │    │ • Classification│
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
      :3000                   :8000                 Redis:6379              Local AI
```

## Component Details

### 1. Frontend (Next.js/TypeScript)
```
Pages:
├── / (Home)
├── /upload (PDF Upload)
└── /analysis (Results, Analysis & Review Dashboard)
    ├── Results Display
    ├── Classification Analysis
    └── Human Feedback Modals

Tech Stack:
• Next.js
• TypeScript + Tailwind CSS
• Real-time status updates
```

### 2. Backend (FastAPI)
```
API Endpoints:
├── POST /api/v1/contracts/upload
├── GET  /api/v1/contracts/{id}/status
├── GET  /api/v1/contracts/{id}/results
├── GET  /api/v1/contracts/{id} (contract details)
├── POST /api/v1/contracts/clauses/feedback
├── GET  /api/v1/health (health check)
└── GET  /docs (Swagger UI)

Database Tables:
├── Contract (main contract data + processing status)
├── FileRecord (file storage tracking)
├── ContractClause (classified clauses + confidence scores)
├── ProcessingLog (audit trail + component logging)
└── ClauseFeedback (human corrections + ratings)
```

### 3. Worker Services (Celery + Redis)
```
Task Queue Architecture:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Upload    │───►│    Redis    │───►│   Worker    │
│   Request   │    │   Message   │    │  Processes  │
│             │    │   Broker    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │  Result     │
                   │  Backend    │
                   │  Storage    │
                   └─────────────┘
```

### 4. Classification Engine
```
NLP Pipeline:
PDF → PyMuPDF → Text Cleaning → Clause Extraction → spaCy Analysis → SBERT Similarity → Classification

Models Used:
• spaCy: en_core_web_sm (NLP pipeline)
• SBERT: all-MiniLM-L6-v2 (semantic similarity)
• RapidFuzz: string matching
• Local processing (no external APIs)
```

## Data Flow Diagram
```
┌─────────────┐
│ User Upload │
│ PDF + State │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────►│  Backend    │────►│   Celery    │
│  Validation │     │  File Save  │     │   Queue     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Database   │◄────│   Results   │◄────│ Stage 1+2   │
│   Storage   │     │  Assembly   │     │ Processing  │
└─────────────┘     └─────────────┘     └─────────────┘
```

## File Storage Structure
```
upload/
├── contracts-tn/
│   ├── {uuid}.pdf                    # Original PDF
│   ├── {uuid}_clauses.json          # Extracted clauses
│   └── {uuid}_results.json          # Classification results
└── contracts-wa/
    ├── {uuid}.pdf
    ├── {uuid}_clauses.json
    └── {uuid}_results.json
```

## Docker Architecture & Scalability Design
```
docker-compose.yml:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  frontend   │  │  backend    │  │   worker    │  │   redis     │
│   :3000     │  │   :8000     │  │  (celery)   │  │   :6379     │
│             │  │             │  │             │  │             │
│ Next.js     │  │ FastAPI     │  │ Processing  │  │ Redis       │
│ React UI    │  │ SQLite DB   │  │ Pipeline    │  │ Message     │
│             │  │             │  │             │  │ Broker      │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
       │                │                │                │
       └────────────────┼────────────────┼────────────────┘
                        │                │
                   hilabs-network (bridge)
                   
Shared Volumes:
• backend_data (SQLite DB + app data)
• worker_uploads (PDF files + processing results)  
• redis_data (Redis persistence)

Scaling Strategy (code can be extended):
• Worker containers are the primary bottleneck (NLP processing: 30-120 sec)
• Horizontal scaling: docker-compose scale worker=N based on Redis queue depth
• Resource allocation: Worker (2 CPU, 4GB) > Backend (1 CPU, 1GB) > Frontend (0.5 CPU, 512MB)
• Auto-scaling triggers: Queue depth >50 tasks → scale up, <10 tasks → scale down
• Current: Single worker container, extensible to multi-worker deployment
```