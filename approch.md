# HiLabs Approach & Methodology

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

*Detailed implementation flowchart available in pipeline.md*
```

## Core Technologies
```
AI/ML Components:
• spaCy NLP → Text processing and analysis
• SBERT → Semantic similarity embeddings  
• RapidFuzz → Lexical string matching
• Local Models → No external API dependencies

*Full technical architecture details in pipeline.md*
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

*Implementation details and thresholds in pipeline.md*
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