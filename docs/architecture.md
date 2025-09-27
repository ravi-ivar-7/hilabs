# Healthcare Contract Language Classification Architecture

## System Overview

```
            ┌────────────────────────┐
            │   Healthcare Contracts │
            │   & Standard Templates │
            │   (TN & WA States)     │
            └──────────┬─────────────┘
                       │
                       ▼
            ┌────────────────────────┐
            │  Data Processing Layer │
            │ - PDF/Text extraction  │
            │ - Clause segmentation  │
            │ - 5 Attribute detection│
            │ - Legal text cleaning  │
            └──────────┬─────────────┘
                       │
                       ▼
            ┌────────────────────────┐
            │  Classification Engine │
            │ - Exact match check    │
            │ - Value substitution   │
            │ - Semantic similarity  │
            │ - Standard vs Non-Std  │
            └──────────┬─────────────┘
                       │
                       ▼
            ┌────────────────────────┐
            │ Analytics & Reporting  │
            │ - Classification stats │
            │ - Contract summaries   │
            │ - Compliance dashboard │
            └────────────────────────┘
```

## Core Components

### 1. Input Layer
- **Contract Documents**: Masked healthcare contracts from TN and WA states
- **Standard Templates**: Gold standard templates for each state
- **Attribute Dictionary**: 5 key attributes to extract and classify

### 2. Processing Pipeline
- **Document Parser**: Extract text from PDF/text formats
- **Clause Extractor**: Identify and segment contract clauses
- **Attribute Detector**: Extract the 5 specified attributes
- **Text Normalizer**: Clean and standardize legal language

### 3. Classification Engine
- **Template Matcher**: Compare extracted clauses with standard templates
- **Similarity Calculator**: Compute semantic and structural similarity
- **Rule Engine**: Apply classification rules (Standard/Non-Standard)
- **Confidence Scorer**: Assign confidence levels to classifications

### 4. Output Layer
- **Summary Metrics**: Total clauses by category
- **Contract Analysis**: Per-contract classification results
- **Audit Trail**: Explainable classification decisions
- **Dashboard**: Visual representation of results

## Technology Stack

### Local Processing (No External APIs)
- **Python 3.9+**: Core language
- **spaCy**: NLP and text processing
- **scikit-learn**: Machine learning algorithms
- **pandas**: Data manipulation
- **PyPDF2/pdfplumber**: PDF text extraction
- **regex**: Pattern matching
- **FastAPI**: APIs

## Data Flow

1. **Input**: Load contracts and templates
2. **Extract**: Parse documents and extract 5 attributes
3. **Compare**: Match extracted clauses with standard templates
4. **Classify**: Determine Standard vs Non-Standard
5. **Report**: Generate summary metrics and detailed results
