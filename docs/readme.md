# HiLabs Hackathon 2025: Healthcare Contract Language Classification

## Project Overview

This project implements an intelligent system to classify healthcare contract clauses as **Standard** or **Non-Standard** by comparing them with template contracts. The solution processes contracts from Tennessee (TN) and Washington (WA) states, extracting 5 key attributes and determining compliance with organizational standards.

## Challenge Summary

- **Input**: Masked healthcare contracts from TN and WA states + Standard templates
- **Output**: Classification of contract clauses as Standard or Non-Standard
- **Constraints**: Local processing only (no external APIs or proprietary LLMs)
- **Focus**: Extract and classify 5 specific attributes defined in the Attribute Dictionary

## Key Features

### 🎯 Core Capabilities
- **Contract Parsing**: Extract text from PDF and text format contracts
- **Clause Segmentation**: Intelligent identification of contract sections and clauses
- **Template Matching**: Compare extracted clauses with standard templates
- **Classification Engine**: Determine Standard vs Non-Standard using multiple methods
- **Performance Optimization**: Memory-efficient processing for 8GB RAM systems

### 🧠 AI-Powered Intelligence
- **Ensemble Classification**: Combine regex, spaCy NER, and semantic similarity
- **Self-Learning System**: Adaptive rules that improve with each contract
- **Legal Domain Expertise**: Healthcare contract-specific intelligence
- **Confidence Scoring**: Transparent accuracy metrics for each classification

### 🔍 Explainability & Compliance
- **Audit Trails**: Complete transparency for legal compliance
- **Human-in-the-Loop**: Flag uncertain classifications for manual review
- **Detailed Reporting**: Summary metrics and per-contract analysis
- **Error Recovery**: Graceful handling of malformed contracts

## Architecture

```
Healthcare Contracts → Data Processing → Classification Engine → Analytics & Reporting
       ↓                      ↓                    ↓                      ↓
   PDF/Text Files      Clause Extraction    Standard vs Non-Std    Summary Metrics
   TN & WA States      5 Attributes         Similarity Matching    Contract Analysis
   Standard Templates  Legal Normalization  Confidence Scoring     Compliance Dashboard
```