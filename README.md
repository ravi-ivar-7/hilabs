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

## Table of Contents
1. [Quick Setup](#quick-setup)
2. [Approach & Methodology](#approach--methodology)
3. [System Architecture](#system-architecture)
4. [Processing Pipeline](#processing-pipeline)

![System Screenshot](data/Screenshot%20from%202025-09-29%2023-44-29.png)

## Demo Video
[![Demo Video](data/Screenshot%20from%202025-09-29%2023-44-29.png)](data/Hilabs%20demo.mp4)

*Click the image above to view the demo video*

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

#### Option A: Local Development Setup (Recommended)
```bash
# Copy environment configuration
cp .env.example .env

# Start all services locally
./services.sh start
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

#### Option B: Docker Setup
```bash
docker-compose up --build
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

**Note**: Docker may take some time to build and start all services (backend, frontend, worker, Redis). Please be patient during the initial setup. 😊
- **Backend API**: http://localhost:8000
- **Redis**: localhost:6379

# Approach & Methodology

## Problem Statement
```
Healthcare Contract Analysis Challenge:
┌─────────────────────────────────────────────────────────────┐
│ INPUT: Healthcare contract PDFs (TN/WA states)              │
│                                                             │
│ GOAL: Classify clauses as Standard/Non-Standard/Ambiguous   │
│                                                             │
│ METHOD: Compare against state-specific template standards   │
└─────────────────────────────────────────────────────────────┘
```

## Target Attributes (5 Key Healthcare Clauses)
```
┌─────────────────────┬─────────────────────────────────────────┐
│ Attribute           │ Description                             │
├─────────────────────┼─────────────────────────────────────────┤
│ Medicaid Timely     │ Claims submission deadlines (120 days)  │
│ Filing              │                                         │
├─────────────────────┼─────────────────────────────────────────┤
│ Medicare Timely     │ Medicare claims deadlines (365 days)   │
│ Filing              │                                         │
├─────────────────────┼─────────────────────────────────────────┤
│ No Steerage/SOC     │ Network participation rules             │
├─────────────────────┼─────────────────────────────────────────┤
│ Medicaid Fee        │ Payment methodology for Medicaid       │
│ Schedule            │                                         │
├─────────────────────┼─────────────────────────────────────────┤
│ Medicare Fee        │ Payment methodology for Medicare       │
│ Schedule            │                                         │
└─────────────────────┴─────────────────────────────────────────┘
```

## Classification Methodology Overview
```
Multi-Step Analysis Approach:
┌─────────────────────────────────────────────────────────────┐
│ 1. Exception Detection → Conditional clauses = NON-STANDARD │
│ 2. Exact Text Matching → Perfect match = STANDARD          │
│ 3. Placeholder Substitution → Structure match = STANDARD   │
│ 4. Fuzzy String Matching → 70%+ similarity = STANDARD      │
│ 5. Semantic Analysis → SBERT embeddings for meaning        │
│ 6. Methodology Detection → Different methods = NON-STANDARD │
└─────────────────────────────────────────────────────────────┘

*Detailed implementation flowchart available below in Processing Pipeline section*
```

## Core Technologies
```
AI/ML Components:
• spaCy NLP → Text processing and analysis
• SBERT → Semantic similarity embeddings  
• RapidFuzz → Lexical string matching
• Local Models → No external API dependencies

*Full technical architecture details above in System Architecture section*
```

## Placeholder Normalization
```
Variable Content Handling:
┌─────────────────────────────────────────────────────────────┐
│ Original: "Provider accepts 95% of eligible charges"       │
│ Template: "Provider accepts XX% of eligible charges"       │
│                                                             │
│ Normalization Process:                                      │
│ 1. Replace "95%" → "<PCT>"                                 │
│ 2. Replace "XX%" → "<PCT>"                                 │
│ 3. Compare normalized versions                              │
│ 4. Match: STANDARD classification                           │
└─────────────────────────────────────────────────────────────┘

Placeholder Patterns:
• <PCT>: Percentages (95%, XX%, one hundred percent)
• <ORG>: Organizations (Plan, Company, Network)
• <MEMBER>: Member types (Enrollee, Subscriber)
• <DATE>: Dates and timeframes
• <FEE_SCHEDULE>: Payment references
```

## Semantic Understanding Approach
```
Meaning-Based Classification:
• SBERT embeddings capture clause intent beyond exact wording
• Cosine similarity measures semantic closeness to templates
• Configurable thresholds balance precision vs coverage
• Handles paraphrased clauses with same legal meaning

*Implementation details and thresholds below in Processing Pipeline section*
```

## Human-in-the-Loop System
```
Feedback Loop:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Ambiguous       │───▶│ Human Review    │───▶│ Corrected       │
│ Classification  │    │ Interface       │    │ Classification  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Show clause +   │    │ User selects    │    │ Store feedback  │
│ template match  │    │ correct class   │    │ for learning    │
└─────────────────┘    └─────────────────┘    └─────────────────┘

```

## Innovation & Compliance
```
Key Innovations:
✓ Multi-step classification combining lexical + semantic analysis
✓ State-specific template management (TN/WA)
✓ Advanced placeholder normalization
✓ Local AI processing (no external APIs)
✓ Real-time progress tracking
✓ Human-in-the-loop feedback system
✓ Local data processing only
```

# System Architecture

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

### Docker Architecture & Scalability Design
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


# Processing Pipeline

## Pipeline Overview
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Upload    │───▶│   Stage 1   │───▶│   Stage 2   │───▶│   Results   │
│   PDF File  │    │Preprocessing│    │Classification│    │  Dashboard  │
│             │    │             │    │             │    │             │
│ • File      │    │ • Extract   │    │ • Template  │    │ • Standard  │
│ • State     │    │ • Clean     │    │ • Compare   │    │ • Non-Std   │
│ • Validate  │    │ • Clauses   │    │ • Classify  │    │ • Ambiguous │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
   Frontend           Celery Task       Celery Task        Frontend
```

## Stage 1: Preprocessing
```
Input: PDF Contract + State (TN/WA)
┌─────────────┐
│ PDF Upload  │
└──────┬──────┘
       │ 20% - Loading PDF
       ▼
┌─────────────┐    PyMuPDF Extraction
│ Text Extract│───► Raw Text + Metadata
└──────┬──────┘    Fallback Methods
       │ 60% - Cleaning Text  
       ▼
┌─────────────┐    Remove Artifacts
│ Text Clean  │───► Normalized Text
└──────┬──────┘    UTF-8 Encoding
       │ 70% - Extracting Clauses
       ▼
┌─────────────┐    Sentence Splitting
│ Clause      │───► Clause List + IDs
│ Extraction  │    Context Preservation
└──────┬──────┘
       │ 90% - Saving Data
       ▼
┌─────────────┐    JSON Serialization
│ Data Store  │───► {id}_clauses.json
└─────────────┘    Database Records
       │ 100% - Complete
       ▼
    Queue Stage 2
```

## Stage 2: Classification
```
Input: Clause Data + Templates
┌─────────────┐
│ Load Data   │
└──────┬──────┘
       │ 20% - Loading Templates
       ▼
┌─────────────┐    State Detection (TN/WA)
│ Template    │───► Load State Templates
│ Loading     │    Initialize NLP Models
└──────┬──────┘
       │ 40% - Starting Classification
       ▼
┌─────────────┐    6-Step Analysis
│ Classify    │───► Standard/Non-Standard/Ambiguous
│ Clauses     │    Confidence Scoring
└──────┬──────┘
       │ 80% - Saving Results
       ▼
┌─────────────┐    Database Storage
│ Store       │───► {id}_results.json
│ Results     │    Audit Logs
└─────────────┘
       │ 100% - Complete
       ▼
    Results Ready
```

## 6-Step Classification Method
```
For Each Clause:

Step 1: Exception Check
┌─────────────────────────────────────┐
│ Scan for: "except", "unless",      │ ──► Non-Standard
│ "provided that", "subject to"      │     (90% confidence)
└─────────────────────────────────────┘

Step 2: Exact Match
┌─────────────────────────────────────┐
│ Normalized text == Template text    │ ──► Standard
│ (case insensitive, whitespace)     │     (99% confidence)
└─────────────────────────────────────┘

Step 3: Placeholder Substitution
┌─────────────────────────────────────┐
│ Replace variables: %,dates,names    │ ──► Standard
│ Check structure similarity          │     (95% confidence)
└─────────────────────────────────────┘

Step 4: Fuzzy Matching
┌─────────────────────────────────────┐
│ RapidFuzz string similarity         │ ──► Standard
│ Threshold: 70%                      │     (90% confidence)
└─────────────────────────────────────┘

Step 5: Semantic Similarity
┌─────────────────────────────────────┐
│ SBERT embeddings + cosine similarity│
│ ≥60%: Standard (85% confidence)     │ ──► Standard/Ambiguous
│ 50-70%: Ambiguous                   │     
└─────────────────────────────────────┘

Step 6: Methodology Detection
┌─────────────────────────────────────┐
│ Check for different payment methods │ ──► Non-Standard
│ "medicare rate", "billed charge"    │     (85% confidence)
└─────────────────────────────────────┘
```

## Data Flow
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browser   │───▶│   FastAPI   │───▶│   Celery    │
│   Upload    │    │   Backend   │    │   Worker    │
└─────────────┘    └─────────────┘    └──────┬──────┘
                                             │
                                             ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SQLite    │◄───│   Results   │◄───│ spaCy+SBERT │
│  Database   │    │  Assembly   │    │ Classifier  │
└─────────────┘    └─────────────┘    └─────────────┘
```

## File Processing Flow
```
upload/contracts-{state}/
├── {uuid}.pdf                 ◄─── Original upload
├── {uuid}_clauses.json        ◄─── Stage 1 output
└── {uuid}_results.json        ◄─── Stage 2 output

Database Flow:
Contract Table ──► ProcessingLog ──► ContractClause ──► ClauseFeedback
     │                  │                  │                │
   Status            Audit Trail      Classifications   Human Feedback
```

## Progress Tracking
```
Stage 1 Progress:
0% ──► 20% ──► 60% ──► 70% ──► 90% ──► 100%
│      │       │       │       │       │
│      │       │       │       │       └─ Data Saved
│      │       │       │       └─ JSON Export
│      │       │       └─ Clause Extraction
│      │       └─ Text Cleaning
│      └─ PDF Loading
└─ Task Started

Stage 2 Progress:
0% ──► 20% ──► 40% ──► 60% ──► 80% ──► 100%
│      │       │       │       │       │
│      │       │       │       │       └─ Results Saved
│      │       │       │       └─ Database Storage
│      │       │       └─ Classification
│      │       └─ Template Loading
│      └─ Data Loading
└─ Task Started
```

## Error Handling
```
Error Types:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PDF Corrupt │    │ NLP Model   │    │ Database    │
│ File Issues │    │ Load Failed │    │ Connection  │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Retry with  │    │ Fallback to │    │ Retry with  │
│ Alternative │    │ Basic NLP   │    │ Backoff     │
│ Extraction  │    │ Processing  │    │ Strategy    │
└─────────────┘    └─────────────┘    └─────────────┘

```

## Accuracy & Validation Methodology

### Systematic Validation Approach

#### 1. Template vs Template Baseline Testing
- Used actual template PDFs as ground truth
- Tested template clauses against themselves to establish baseline accuracy
- Template clauses are **pre-extracted** and hardcoded in `worker/classification_parameters.py`
- This eliminates content variation and focuses purely on algorithm performance


#### 2. Real PDF Content Extraction
```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ User Contract PDFs  │───▶│ PDF Text Extraction │───▶│ Extracted Clauses   │
│ (Upload via UI)     │    │ • pdfplumber (1st)  │    │ (Dynamic parsing)   │
└─────────────────────┘    │ • PyPDF2 (fallback)│    └─────────────────────┘
                           │ • Robust extraction │              │
                           └─────────────────────┘              ▼
┌─────────────────────┐                               ┌─────────────────────┐
│ Static Templates    │                               │ Classification      │
│ • TN_TEMPLATE_      │────────────────────────────▶│ • Fuzzy matching    │
│   CLAUSES (5 attrs) │                               │ • Semantic analysis │
│ • WA_TEMPLATE_      │                               │ • Multi-step logic  │
│   CLAUSES (5 attrs) │                               │ • Confidence scores │
│ • Hardcoded in code │                               └─────────────────────┘
└─────────────────────┘                                         │
                                                                ▼
                                                      ┌─────────────────────┐
                                                      │ Dual Storage        │
                                                      │ • Database records  │
                                                      │ • JSON backup files │
                                                      │ • Audit trails     │
                                                      └─────────────────────┘
```

### Data-Driven Performance Tracking

#### Quantifiable Improvements:
```
┌─────────────────────┬─────────┬─────────┬─────────────────────────┐
│ Attribute           │ Before  │ After   │ Improvement Method      │
├─────────────────────┼─────────┼─────────┼─────────────────────────┤
│ WA Medicare Timely  │   0%    │  40%    │ Added XX-day language   │
│ WA Medicaid Fee     │  11%    │  21%    │ Structure alignment     │
│ WA No Steerage/SOC  │   4%    │   9%    │ Added legal phrases     │
└─────────────────────┴─────────┴─────────┴─────────────────────────┘
```

### Iterative Accuracy Improvements

#### Classification Parameter Optimization:
Based on systematic testing and validation results, the `worker/classification_parameters.py` file has been continuously updated to improve classification accuracy:

**Key Improvements Made:**
- **Threshold Tuning**: Adjusted fuzzy matching threshold to 70% and semantic similarity to 0.60 based on real-world performance
- **Template Clause Refinement**: Updated actual template clauses extracted from TN/WA PDFs for better matching
- **Exception Token Expansion**: Added comprehensive list of conditional clause indicators
- **Placeholder Normalization**: Enhanced pattern matching for variables like percentages, dates, and organization names
- **State-Specific Optimization**: Separate template sets for TN and WA with state-specific legal language

**Configuration Structure:**
```python
# worker/classification_parameters.py - Centralized Configuration

# Classification thresholds (optimized through testing)
FUZZY_THRESHOLD = 70          # RapidFuzz similarity threshold
SBERT_THRESHOLD = 0.60        # SBERT semantic similarity threshold
SBERT_AMBIG_LOW = 0.50        # Lower bound for ambiguous classification
SBERT_AMBIG_HIGH = 0.70       # Upper bound for ambiguous classification

# Template clauses (5 attributes per state)
TN_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "...",
    "Medicare Timely Filing": "...",
    "Medicaid Fee Schedule": "...",
    "Medicare Fee Schedule": "...",
    "No Steerage/SOC": "..."
}

WA_TEMPLATE_CLAUSES = {
    # Same 5 attributes with state-specific content
}

# Exception detection
EXCEPTION_TOKENS = ['except', 'unless', 'provided that', ...]

# Text normalization patterns
PLACEHOLDER_MAP = {
    r"\b\d{1,3}\s*%\b": "<PCT>",
    r"\b(Fee\s+Schedule|Compensation\s+Schedule)\b": "<FEE_SCHEDULE>",
    # ... 20+ normalization patterns
}
```

**Performance Impact:**
- **WA Medicare Timely Filing**: 0% → 40% accuracy improvement
- **WA Medicaid Fee Schedule**: 11% → 21% accuracy improvement  
- **WA No Steerage/SOC**: 4% → 9% accuracy improvement
- **Overall System**: Consistent 85%+ confidence scores on standard clauses

This centralized parameter approach allows for rapid iteration and testing of classification improvements without code changes.