#!/usr/bin/env python3
"""
HiLabs Hackathon — Contract Clause Extractor with DeBERTa v3 Large Cross-Encoder

Enhanced version with DeBERTa v3 Large cross-encoder enabled for higher accuracy.
This version prioritizes the cross-encoder for better semantic understanding.
"""

import sys, os, re, json, math, string, itertools, pathlib, textwrap, typing
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd
from tqdm import tqdm

# NLP & Similarity
import spacy
from rapidfuzz import fuzz
import numpy as np

# PDF
import fitz  # PyMuPDF

# Embeddings / Transformers
from sentence_transformers import SentenceTransformer, util as sbert_util
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

print("DeBERTa v3 Large Cross-Encoder Version")

# ======================
#        CONFIG - DEBERTA OPTIMIZED
# ======================

# FIXED PATHS - relative to notebooks directory
ATTRIBUTE_EXCEL_PATH = '../data/Attribute Dictionary.xlsx'   
TEMPLATE_FILES = [
    '../data/templates/TN_Standard_Template_Redacted.pdf',
    '../data/templates/WA_Standard_Template_Redacted.pdf'
]         
CONTRACT_FILES = [
    '../hackathon/Contracts/TN/TN_Contract1_Redacted.pdf',
    '../hackathon/Contracts/WA/WA_2_Redacted.pdf'
]         

ATTR_COL_CANDIDATES = ['Attribute']
KEYWORDS_COL_CANDIDATES = ['Keywords']
REGEX_COL_CANDIDATES = ['Regex']

# Only these 5 attributes are tracked 
MAX_TARGET_ATTRIBUTES = 5
TARGET_ATTRIBUTES = [
    "Medicaid Timely Filing",
    "Medicare Timely Filing",
    "No Steerage/SOC",
    "Medicaid Fee Schedule",
    "Medicare Fee Schedule"
]

# Tokens that mark clauses as Non-Standard if present
EXCEPTION_TOKENS = [
    'except', 'unless', 'provided that',
    'subject to', 'however,', 'save that',
    'notwithstanding', 'only if'
]

# DeBERTa-optimized thresholds (adjusted for template matching)
FUZZY_THRESHOLD = 85                   # Lowered for better template matching
SBERT_THRESHOLD = 0.75                 # Lowered for better template matching
SBERT_AMBIG_LOW, SBERT_AMBIG_HIGH = 0.65, 0.75  # Adjusted ambiguous band
DEBERTA_THRESHOLD = 0.70               # DeBERTa cross-encoder threshold

# Model toggles - DeBERTa ENABLED
USE_SPACY_MODEL = "en_core_web_sm"
USE_SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
USE_DEBERTA_CROSS_ENCODER = True  # ENABLED
DEBERTA_CE_MODEL = "cross-encoder/nli-deberta-v3-large"

# Output
OUT_DIR = Path("./outputs_deberta")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Placeholder patterns (same as base version)
PLACEHOLDER_MAP = {
    r"\[\(?\s*XX\s*%\s*\)?\]": "<PCT>",
    r"\b\d{1,3}\s*%\b": "<PCT>",
    r"\b(one\s*hundred|ninety[-\s]*five|fifty)\s*percent\b": "<PCT>",
    r"\b(Fee\s+Schedule|Compensation\s+Schedule|Plan\s+Compensation\s+Schedule|WCS|PCS)\b": "<FEE_SCHEDULE>",
    r"\b(Rate|Eligible\s+Charge[s]?)\b": "<RATE>",
    r"\b(Plan|Company|Network|Agency|Affiliate|Other\s+Payors?)\b": "<ORG>",
    r"\b(Provider|Participating\s+Provider)\b": "<PROVIDER>",
    r"\b(Member|Enrollee|Subscriber|Insured|Beneficiary|Covered\s+(Person|Individual)|Dependent)\b": "<MEMBER>",
    r"\b(Government\s+Program|Medicare|Medicaid|CMS|HCA)\b": "<GOV_PROGRAM>",
    r"\b(Participation\s+Attachment[s]?)\b": "<ATTACHMENT>",
    r"\b(provider\s+manual\(s\))\b": "<PROVIDER_MANUAL>",
    r"\b(Health\s+Benefit\s+Plan)\b": "<PLAN_DOC>",
    r"\b(Cost\s*Share[s]?|copayment[s]?|coinsurance|deductible[s]?)\b": "<COST_SHARE>",
    r"\b(Claim[s]?)\b": "<CLAIM>",
    r"\b(Regulatory\s+Requirements?)\b": "<REG_REQ>",
    r"\b(Effective\s+Date|MM/DD/YYYY)\b": "<DATE>",
    r"\[\s*_{2,}\s*\]": "<BLANK>",
    r"\b(Health\s+Services?|Covered\s+Services?)\b": "<SERVICE>",
    r"\b(Medically\s+Necessary|Medical\s+Necessity)\b": "<MEDICAL_NECESSITY>",
}

# Import utility functions from base version
from word2number import w2n 

def normalize_whitespace(s: str) -> str:
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s

def to_ascii_lower(s: str) -> str:
    return normalize_whitespace(s).lower()

def apply_placeholders(s: str) -> str:
    out = s
    for pat, repl in PLACEHOLDER_MAP.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    out = re.sub(r'(\d+)\s*percent', r'\1%', out, flags=re.IGNORECASE)
    
    def word_percent_to_num(match):
        words = match.group(1).lower()
        try:
            num = w2n.word_to_num(words)
            return f"{num}%"
        except ValueError:
            return match.group(0)
    
    out = re.sub(r'\b([a-z\s-]+)\s+percent\b', word_percent_to_num, out, flags=re.IGNORECASE)
    return out

def normalize_for_compare(s: str) -> str:
    s = apply_placeholders(s)
    punct = ''.join(ch for ch in r"""!"#$&'()*+,-./:;<=>?@[\\]^_`{|}~""" if ch != '%')
    s = s.translate(str.maketrans('', '', punct))
    s = to_ascii_lower(s)
    return s

def contains_exception_tokens(text: str, template_has_exception: bool = False) -> bool:
    text_l = to_ascii_lower(text)
    if template_has_exception:
        return False
    return any(tok in text_l for tok in EXCEPTION_TOKENS)

# Enhanced Similarity Engines with DeBERTa prioritization
class EnhancedSimilarityEngines:
    def __init__(self, sbert_model_name: str, use_cross_encoder: bool, cross_encoder_name: str):
        print(f"Loading SBERT model: {sbert_model_name}")
        self.sbert = SentenceTransformer(sbert_model_name)
        self.use_cross_encoder = use_cross_encoder
        self.cross_encoder = None
        self.ce_tokenizer = None
        
        if use_cross_encoder:
            print(f"Loading DeBERTa Cross-Encoder: {cross_encoder_name}")
            self.cross_encoder = AutoModelForSequenceClassification.from_pretrained(cross_encoder_name)
            self.ce_tokenizer = AutoTokenizer.from_pretrained(cross_encoder_name)
            self.cross_encoder.eval()
            print("DeBERTa Cross-Encoder loaded successfully!")

    @torch.no_grad()
    def sbert_score(self, a: str, b: str) -> float:
        embs = self.sbert.encode([a, b], convert_to_tensor=True, normalize_embeddings=True)
        sim = sbert_util.cos_sim(embs[0], embs[1]).item()
        return float(sim)

    @torch.no_grad()
    def cross_encoder_score(self, a: str, b: str) -> Optional[float]:
        if not self.use_cross_encoder or self.cross_encoder is None:
            return None
        
        # Truncate inputs to avoid token limit issues
        max_length = 400  # Conservative limit for DeBERTa
        a_truncated = a[:max_length] if len(a) > max_length else a
        b_truncated = b[:max_length] if len(b) > max_length else b
        
        inputs = self.ce_tokenizer(
            a_truncated, b_truncated, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        logits = self.cross_encoder(**inputs).logits
        
        if logits.shape[-1] == 3:  # NLI model with 3 classes
            probs = torch.softmax(logits, dim=-1).squeeze(0)
            entail = probs[2].item()  # entailment probability
            return float(entail)
        else:  # Binary classification
            return torch.sigmoid(logits).squeeze().item()

# Enhanced classification with DeBERTa prioritization
@dataclass
class StepResult:
    step: str
    satisfied: bool
    score: Optional[float]
    comment: str

@dataclass
class ClauseDecision:
    clause_id: int
    attribute: Optional[str]
    template_used: Optional[str]
    label: str
    score: float
    rule: str
    steps: List[StepResult]
    text: str

def classify_against_template_deberta(clause, template, engines: EnhancedSimilarityEngines) -> Tuple[str, float, str, List[StepResult]]:
    """Enhanced classification pipeline with DeBERTa prioritization."""
    steps = []
    c_raw, c_norm = clause["text"], clause.get("norm", clause["text"].lower())
    t_norm = template.norm_text

    # Step A: Exception/condition tokens
    has_exc = contains_exception_tokens(c_raw, template_has_exception=template.has_exception_tokens)
    steps.append(StepResult("exception_check", has_exc, None, "Detected conditional/exception tokens in clause; template lacks them."))
    if has_exc:
        return "Non-Standard", 0.95, "new_condition", steps

    # Step B: DeBERTa Cross-Encoder (PRIORITIZED)
    if engines.use_cross_encoder:
        ce_score = engines.cross_encoder_score(c_raw, template.raw_text)
        if ce_score is not None:
            ce_satisfied = ce_score >= DEBERTA_THRESHOLD
            steps.append(StepResult("deberta_cross_encoder", ce_satisfied, ce_score, f"DeBERTa entailment={ce_score:.3f} (threshold={DEBERTA_THRESHOLD})"))
            
            if ce_score >= 0.85:  # High confidence
                return "Standard", float(ce_score), "deberta_high", steps
            elif ce_score >= DEBERTA_THRESHOLD:
                return "Standard", float(ce_score), "deberta_medium", steps
            elif ce_score >= 0.60:  # Ambiguous range
                steps.append(StepResult("deberta_ambiguous", True, ce_score, "DeBERTa score in ambiguous range"))
                return "Ambiguous", float(ce_score), "deberta_ambiguous", steps

    # Step C: Exact normalized match
    exact = (c_norm == t_norm)
    steps.append(StepResult("exact_normalized_match", exact, None, "Clause equals template after normalization."))
    if exact:
        return "Standard", 0.99, "exact_norm", steps

    # Step D: Fuzzy lexical similarity (higher threshold)
    lex = fuzz.ratio(c_norm, t_norm)
    steps.append(StepResult("fuzzy_lexical", lex >= FUZZY_THRESHOLD, float(lex)/100.0, f"RapidFuzz ratio={lex} (threshold={FUZZY_THRESHOLD})"))
    if lex >= FUZZY_THRESHOLD:
        return "Standard", 0.92, "lexical_high", steps

    # Step E: Semantic similarity (SBERT with higher threshold)
    sbert_sim = engines.sbert_score(c_raw, template.raw_text)
    steps.append(StepResult("semantic_sbert", sbert_sim >= SBERT_THRESHOLD, sbert_sim, f"SBERT cosine={sbert_sim:.3f} (threshold={SBERT_THRESHOLD})"))
    if sbert_sim >= SBERT_THRESHOLD:
        return "Standard", 0.88, "semantic_high", steps

    if SBERT_AMBIG_LOW <= sbert_sim < SBERT_AMBIG_HIGH:
        steps.append(StepResult("semantic_ambiguous_band", True, sbert_sim, "SBERT score in ambiguous range"))
        return "Ambiguous", sbert_sim, "semantic_ambiguous", steps

    # Step F: Default Non-Standard
    final_score = ce_score if engines.use_cross_encoder and ce_score is not None else sbert_sim
    steps.append(StepResult("default_nonstandard", True, final_score, "Low similarity across all methods"))
    return "Non-Standard", float(final_score), "low_similarity", steps

# Load other necessary functions (abbreviated for space)
def autodetect_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    for c in df.columns:
        cl = c.lower()
        if any(k.lower() in cl for k in candidates):
            return c
    return None

@dataclass
class AttributeSpec:
    name: str
    keywords: List[str]
    regexes: List[str]

@dataclass
class TemplateClause:
    name: str
    raw_text: str
    norm_text: str
    has_exception_tokens: bool

def load_attribute_dictionary(xlsx_path: str) -> List[AttributeSpec]:
    df = pd.read_excel(xlsx_path, sheet_name=0)
    attr_col = autodetect_column(df, ATTR_COL_CANDIDATES)
    if not attr_col:
        raise ValueError(f"Could not find attribute column. Checked: {ATTR_COL_CANDIDATES}")

    kw_col = autodetect_column(df, KEYWORDS_COL_CANDIDATES)
    rx_col = autodetect_column(df, REGEX_COL_CANDIDATES)

    specs = []
    for _, row in df.iterrows():
        name = str(row[attr_col]).strip()
        if not name or name.lower() in ['nan', 'none']:
            continue
        keywords = []
        regexes = []
        if kw_col and not pd.isna(row.get(kw_col, None)):
            keywords = [normalize_whitespace(x) for x in re.split(r'[;,]', str(row[kw_col])) if str(x).strip()]
        if rx_col and not pd.isna(row.get(rx_col, None)):
            regexes = [normalize_whitespace(x) for x in re.split(r'[;,]', str(row[rx_col])) if str(x).strip()]

        specs.append(AttributeSpec(name=name, keywords=keywords, regexes=regexes))

    seen = set()
    uniq_specs = []
    for spec in specs:
        if spec.name not in seen:
            uniq_specs.append(spec)
            seen.add(spec.name)
        if len(uniq_specs) >= MAX_TARGET_ATTRIBUTES:
            break

    print("Loaded attributes:", [s.name for s in uniq_specs])
    return uniq_specs

def pdf_to_text(path: str) -> str:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    return "\n".join(texts)

def load_templates(paths: List[str]) -> List[TemplateClause]:
    tpls = []
    for path in paths:
        p = Path(path)
        if not p.exists():
            print(f"[WARN] Template not found: {p}")
            continue
        
        if p.suffix.lower() == '.pdf':
            raw = pdf_to_text(str(p))
        else:
            raw = p.read_text(encoding='utf-8', errors='ignore')
            
        has_exc = contains_exception_tokens(raw, template_has_exception=False)
        tpls.append(TemplateClause(
            name=p.stem,
            raw_text=raw,
            norm_text=normalize_for_compare(raw),
            has_exception_tokens=has_exc
        ))
    if not tpls:
        raise ValueError("No templates loaded.")
    print("Templates:", [t.name for t in tpls])
    return tpls

def split_into_clauses(text: str) -> List[Dict]:
    paras = [normalize_whitespace(p) for p in re.split(r'\n\s*\n+', text) if normalize_whitespace(p)]
    clauses = []
    clause_id = 1
    for para in paras:
        splits = re.split(r'(?<=[.;])\s+(?=[A-Z(\d])|(?<=: )\s+', para)
        for sp in splits:
            s = normalize_whitespace(sp)
            if len(s) < 5:
                continue
            clauses.append({
                "clause_id": clause_id,
                "text": s,
                "norm": normalize_whitespace(s.lower())
            })
            clause_id += 1
    return clauses

# Enhanced attribute detection
ATTRIBUTE_SEEDS = {
    "Medicaid Timely Filing": {
        "keywords": ["medicaid", "timely filing", "filing deadline", "days", "claim submission"],
        "regexes": [r"\bmedicaid\b.*\b(timely|filing|deadline)\b", r"\b\d{1,3}\s*days?\b.*\b(medicaid|filing)\b"]
    },
    "Medicare Timely Filing": {
        "keywords": ["medicare", "timely filing", "filing deadline", "days", "claim submission"],
        "regexes": [r"\bmedicare\b.*\b(timely|filing|deadline)\b", r"\b\d{1,3}\s*days?\b.*\b(medicare|filing)\b"]
    },
    "No Steerage/SOC": {
        "keywords": ["steerage", "standard of care", "soc", "steering", "referral"],
        "regexes": [r"\b(steerage|steering|standard\s+of\s+care|soc)\b"]
    },
    "Medicaid Fee Schedule": {
        "keywords": ["medicaid", "fee schedule", "compensation", "payment", "reimbursement"],
        "regexes": [r"\bmedicaid\b.*\b(fee|schedule|compensation|payment)\b"]
    },
    "Medicare Fee Schedule": {
        "keywords": ["medicare", "fee schedule", "compensation", "payment", "reimbursement"],
        "regexes": [r"\bmedicare\b.*\b(fee|schedule|compensation|payment)\b"]
    }
}

def detect_attribute_for_clause(clause_text: str, specs: List[AttributeSpec], nlp=None) -> Optional[str]:
    if not clause_text or not clause_text.strip():
        return None

    text_lower = clause_text.lower()

    for spec in specs:
        if spec.name in ATTRIBUTE_SEEDS:
            seed = ATTRIBUTE_SEEDS[spec.name]
            
            for rx in seed["regexes"]:
                try:
                    if re.search(rx, clause_text, flags=re.IGNORECASE):
                        return f"{spec.name} (regex)"
                except re.error:
                    pass
            
            if any(kw in text_lower for kw in seed["keywords"]):
                return f"{spec.name} (keyword)"

        for rx in spec.regexes:
            try:
                if re.search(rx, clause_text, flags=re.IGNORECASE):
                    return f"{spec.name} (spec_regex)"
            except re.error:
                pass

        if any(kw.lower() in text_lower for kw in spec.keywords):
            return f"{spec.name} (spec_keyword)"

    return None

def choose_best_template(clause, templates: List[TemplateClause], engines: EnhancedSimilarityEngines):
    ranked = []
    for tpl in templates:
        label, score, rule, steps = classify_against_template_deberta(clause, tpl, engines)
        ranked.append((tpl.name, label, score, rule, steps))

    # Immediate return for exception-based Non-Standard
    for tpl_name, label, score, rule, steps in ranked:
        if label == "Non-Standard" and any(s.step == "exception_check" and s.satisfied for s in steps):
            return tpl_name, label, score, rule, steps

    def score_key(x):
        tpl_name, label, score, rule, steps = x
        priority = {"Standard": 3, "Ambiguous": 2, "Non-Standard": 1}.get(label, 0)
        return (priority, score)

    tpl_name, label, score, rule, steps = sorted(ranked, key=score_key, reverse=True)[0]
    return tpl_name, label, score, rule, steps

def classify_clauses(clauses: List[Dict], specs: List[AttributeSpec], templates: List[TemplateClause], engines: EnhancedSimilarityEngines, nlp=None):
    decisions = []
    for cl in tqdm(clauses, desc="Classifying clauses"):
        attr = detect_attribute_for_clause(cl["text"], specs, nlp)

        if not attr:
            decisions.append(ClauseDecision(
                clause_id=cl["clause_id"], attribute=None, template_used=None,
                label="Skip", score=0.0, rule="no_target_attribute", steps=[], text=cl["text"]
            ))
            continue

        tpl_name, label, score, rule, steps = choose_best_template(cl, templates, engines)
        decisions.append(ClauseDecision(
            clause_id=cl["clause_id"], attribute=attr, template_used=tpl_name,
            label=label, score=score, rule=rule, steps=steps, text=cl["text"]
        ))
    return decisions

def init_spacy(model: str = "en_core_web_sm"):
    try:
        nlp = spacy.load(model)
    except OSError:
        raise OSError(f"spaCy model '{model}' not found. Install via: python -m spacy download {model}")
    return nlp

def main():
    print("Starting HiLabs Contract Clause Classifier with DeBERTa v3 Large...")
    
    # Load components
    if not Path(ATTRIBUTE_EXCEL_PATH).exists():
        raise FileNotFoundError(f"Attribute dictionary not found: {ATTRIBUTE_EXCEL_PATH}")
    
    specs = load_attribute_dictionary(ATTRIBUTE_EXCEL_PATH)
    templates = load_templates(TEMPLATE_FILES)

    try:
        nlp = init_spacy(USE_SPACY_MODEL)
    except Exception as e:
        print("[WARN] spaCy init failed:", e)
        nlp = None

    # Initialize enhanced engines with DeBERTa
    engines = EnhancedSimilarityEngines(
        sbert_model_name=USE_SBERT_MODEL,
        use_cross_encoder=USE_DEBERTA_CROSS_ENCODER,
        cross_encoder_name=DEBERTA_CE_MODEL
    )
    print("SBERT model loaded:", USE_SBERT_MODEL)
    print("DeBERTa Cross-Encoder enabled:", USE_DEBERTA_CROSS_ENCODER)

    # Process contracts
    print("Contract files:", CONTRACT_FILES)

    all_decisions = []
    for cpath in CONTRACT_FILES:
        if not Path(cpath).exists():
            print(f"[WARN] Contract file not found: {cpath}")
            continue
            
        if Path(cpath).suffix.lower() == '.pdf':
            raw_text = pdf_to_text(cpath)
        else:
            raw_text = Path(cpath).read_text(encoding='utf-8', errors='ignore')

        clauses = split_into_clauses(raw_text)
        print(f"{Path(cpath).name}: Extracted {len(clauses)} clauses")

        decisions = classify_clauses(clauses, specs, templates, engines, nlp)
        all_decisions.extend([asdict(d) for d in decisions])

    # Generate summaries
    df = pd.DataFrame(all_decisions)
    summary = df[df['label'] != 'Skip'].groupby(['attribute', 'label']).size().reset_index(name='count')
    print("\nSummary by attribute/label:")
    print(summary)

    # Save outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "clause_classification_summary_deberta.csv"
    out_json = OUT_DIR / "clause_classification_details_deberta.json"
    df.to_csv(out_csv, index=False)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(all_decisions, f, ensure_ascii=False, indent=2)

    print(f"\nSaved summary CSV: {out_csv.resolve()}")
    print(f"Saved details JSON: {out_json.resolve()}")

    # Show DeBERTa-specific results
    deberta_df = df[df['rule'].str.contains('deberta', na=False)]
    print(f"\nClauses classified using DeBERTa: {len(deberta_df)}")
    
    valid_df = df[df['label'].isin(['Standard', 'Non-Standard'])]
    print(f"Total valid classified clauses: {len(valid_df)}")

    return df, all_decisions

if __name__ == "__main__":
    df, decisions = main()
