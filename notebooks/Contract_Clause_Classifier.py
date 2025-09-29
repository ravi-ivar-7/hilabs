#!/usr/bin/env python3
"""
Contract Clause Extractor & Standard/Non‑Standard Classifier

Classifies healthcare contract clauses against standard templates using NLP techniques.
"""

import sys, os, re, json, math, string, itertools, pathlib, textwrap, typing
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd
from tqdm import tqdm

import spacy
from rapidfuzz import fuzz
import numpy as np
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util as sbert_util
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

try:
    from google.colab import files
    ON_COLAB = True
except Exception:
    ON_COLAB = False

print("ON_COLAB:", ON_COLAB)

# Configuration

TEMPLATE_FILES = [
    '../data/templates/TN_Standard_Template_Redacted.pdf',
    '../data/templates/WA_Standard_Template_Redacted.pdf'
]         
CONTRACT_FILES = [
    '../hackathon/Contracts/TN/TN_Contract1_Redacted.pdf',
    '../hackathon/Contracts/TN/TN_Contract2_Redacted.pdf',
    '../hackathon/Contracts/TN/TN_Contract3_Redacted.pdf',
    '../hackathon/Contracts/WA/WA_1_Redacted.pdf',
    '../hackathon/Contracts/WA/WA_2_Redacted.pdf'
]         

TARGET_ATTRIBUTES = [
    "Medicaid Timely Filing",
    "Medicare Timely Filing", 
    "No Steerage/SOC",
    "Medicaid Fee Schedule",
    "Medicare Fee Schedule"
]

EXCEPTION_TOKENS = [
    'except', 'unless', 'provided that',
    'subject to', 'however,', 'save that',
    'notwithstanding', 'only if'
]

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

FUZZY_THRESHOLD = 85
SBERT_THRESHOLD = 0.75
SBERT_AMBIG_LOW, SBERT_AMBIG_HIGH = 0.65, 0.75

USE_SPACY_MODEL = "en_core_web_sm"
USE_SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
USE_DEBERTA_CROSS_ENCODER = False
DEBERTA_CE_MODEL = "cross-encoder/nli-deberta-v3-large"

OUT_DIR = Path("./outputs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Utility Functions

from word2number import w2n 

def normalize_whitespace(s: str) -> str:
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s

def normalize_for_matching(s: str) -> str:
    """Enhanced normalization for better clause matching."""
    s = normalize_whitespace(s).lower()
    s = re.sub(r'[^\w\s%$-]', ' ', s)
    s = re.sub(r'\b\d+(\.\d+)?\b(?!%)', 'NUM', s)
    s = re.sub(r'\bNUM\s*\.\s*NUM\b', 'SECTION', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def to_ascii_lower(s: str) -> str:
    return normalize_whitespace(s).lower()

def apply_placeholders(s: str) -> str:
    """Replace known placeholders to canonical tokens for fair comparison."""
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

# Template Loading

@dataclass
class TemplateClause:
    name: str
    attribute: str
    raw_text: str
    norm_text: str
    has_exception_tokens: bool

TN_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility",
    "Medicare Timely Filing": "Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility. 3.1.1 In situations of enrollment in with a retroactive eligibility date, the time frames for filing a claim shall begin on the date that receives notification from of the Medicaid Member's eligibility/enrollment.",
    "No Steerage/SOC": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment",
    "Medicaid Fee Schedule": "one hundred percent (100%) of Eligible Charges for Covered Services, or the total reimbursement amount that Provider and have agreed upon as set forth in the Compensation Schedule. The Rate includes applicable Cost Shares, and shall represent payment in full to Provider for Covered Services.",
    "Medicare Fee Schedule": "Medicare Advantage Network means Network of Providers that provides MA Covered Services to MA Members. Related Entity(ies) means any entity that is related to by common ownership or control and performs some of management functions under contract or delegation."
}

WA_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "Provider must submit a request for an adjustment to Plan in accordance with the provider manual(s). Provider shall be solely responsible to the Member for treatment, medical care, and advice with respect to the provision of Health Services.",
    "Medicare Timely Filing": "Provider shall submit Claims to Plan, using appropriate and current Coded Service Identifier(s), within three hundred sixty-five (365) days from the date the Health Services are rendered or Plan may refuse payment. If Plan is the secondary payor, the three hundred sixty-five (365) day period will not begin until Provider receives notification of primary payor's responsibility.",
    "No Steerage/SOC": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment",
    "Medicaid Fee Schedule": "one hundred percent (100%) of Eligible Charges for Covered Services, or the total reimbursement amount that Provider and have agreed upon as set forth in the Compensation Schedule. The Rate includes applicable Cost Shares, and shall represent payment in full to Provider for Covered Services.",
    "Medicare Fee Schedule": "Medicare Advantage Network means Network of Providers that provides MA Covered Services to MA Members. Related Entity(ies) means any entity that is related to by common ownership or control and performs some of management functions under contract or delegation."
}

def read_text_file(p: Path) -> str:
    return p.read_text(encoding='utf-8', errors='ignore')

def pdf_to_text(path: str) -> str:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text("text"))
    return "\n".join(texts)

def load_templates(paths: List[str]) -> List[TemplateClause]:
    """Load template clauses from hardcoded dictionaries."""
    tpls = []
    
    for path in paths:
        state = "TN" if "TN" in str(path) else "WA"
        
        if state == "TN":
            template_clauses = TN_TEMPLATE_CLAUSES
        else:
            template_clauses = WA_TEMPLATE_CLAUSES
        
        for attribute, clause_text in template_clauses.items():
            has_exc = contains_exception_tokens(clause_text, template_has_exception=False)
            tpls.append(TemplateClause(
                name=f"{state}_{attribute.replace(' ', '_')}",
                attribute=attribute,
                raw_text=clause_text,
                norm_text=normalize_for_matching(clause_text),
                has_exception_tokens=has_exc
            ))
    
    if not tpls:
        raise ValueError("No templates loaded. Please provide template files.")
    
    print("Templates:", [f"{t.name} ({t.attribute})" for t in tpls])
    return tpls

# Contract Processing

def is_pdf(path: str) -> bool:
    return Path(path).suffix.lower() == '.pdf'

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
                "norm": normalize_for_matching(s)
            })
            clause_id += 1
    return clauses

# Attribute Detection

ATTRIBUTE_SEEDS = {
    "Medicaid Timely Filing": {
        "keywords": ["medicaid", "timely filing", "claims", "submission", "days", "claim", "billing"],
        "regexes": [r"\bmedicaid\b.*\b(timely\s+filing|claims?\s+submission|filing\s+deadline)\b", 
                   r"\btimely\s+filing\b.*\bmedicaid\b",
                   r"\bclaims?\b.*\bmedicaid\b.*\b(days?|deadline|filing)\b"],
        "required_context": ["filing", "submission", "deadline", "days"],
        "exclude_context": ["beneficiary", "eligibility", "enrollment", "member"]
    },
    "Medicare Timely Filing": {
        "keywords": ["medicare", "timely filing", "claims", "submission", "days", "claim", "billing"],
        "regexes": [r"\bmedicare\b.*\b(timely\s+filing|claims?\s+submission|filing\s+deadline)\b",
                   r"\btimely\s+filing\b.*\bmedicare\b", 
                   r"\bclaims?\b.*\bmedicare\b.*\b(days?|deadline|filing)\b"],
        "required_context": ["filing", "submission", "deadline", "days"],
        "exclude_context": ["beneficiary", "eligibility", "enrollment", "member"]
    },
    "No Steerage/SOC": {
        "keywords": ["steerage", "soc", "freedom", "choice", "referral", "network"],
        "regexes": [r"\b(no\s+steerage|anti-steerage|steerage\s+prohibition)\b",
                   r"\bfreedom\s+of\s+choice\b",
                   r"\breferral\s+(restriction|requirement|prohibition)\b"],
        "required_context": ["choice", "referral", "network", "provider"],
        "exclude_context": []
    },
    "Medicaid Fee Schedule": {
        "keywords": ["medicaid", "fee schedule", "payment", "reimbursement", "fee", "schedule", "rate"],
        "regexes": [r"\bmedicaid\b.*\b(fee\s+schedule|payment\s+rate|reimbursement\s+rate)\b",
                   r"\bfee\s+schedule\b.*\bmedicaid\b",
                   r"\bmedicaid\b.*\breimbursement\b.*\b(rate|amount|schedule)\b"],
        "required_context": ["fee", "payment", "reimbursement", "rate", "schedule"],
        "exclude_context": ["beneficiary", "eligibility", "enrollment"]
    },
    "Medicare Fee Schedule": {
        "keywords": ["medicare", "fee schedule", "payment", "reimbursement", "fee", "schedule", "rate"],
        "regexes": [r"\bmedicare\b.*\b(fee\s+schedule|payment\s+rate|reimbursement\s+rate)\b",
                   r"\bfee\s+schedule\b.*\bmedicare\b",
                   r"\bmedicare\b.*\breimbursement\b.*\b(rate|amount|schedule)\b"],
        "required_context": ["fee", "payment", "reimbursement", "rate", "schedule"],
        "exclude_context": ["beneficiary", "eligibility", "enrollment"]
    }
}

def validate_contextual_match(clause_text: str, attribute_name: str, sbert_model=None) -> bool:
    """Simplified validation - just check basic keyword presence."""
    clause_lower = clause_text.lower()
    
    # Basic keyword checks for each attribute
    if "medicaid timely filing" in attribute_name.lower():
        return "medicaid" in clause_lower and any(word in clause_lower for word in ["filing", "claim", "submission", "days"])
    elif "medicare timely filing" in attribute_name.lower():
        return "medicare" in clause_lower and any(word in clause_lower for word in ["filing", "claim", "submission", "days"])
    elif "no steerage" in attribute_name.lower():
        return any(word in clause_lower for word in ["steerage", "choice", "referral", "network", "provider"])
    elif "medicaid fee schedule" in attribute_name.lower():
        return "medicaid" in clause_lower and any(word in clause_lower for word in ["fee", "schedule", "payment", "rate"])
    elif "medicare fee schedule" in attribute_name.lower():
        return "medicare" in clause_lower and any(word in clause_lower for word in ["fee", "schedule", "payment", "rate"])
    
    return True

def detect_attribute_for_clause_spacy_regex(
    clause_text: str, attribute_names: List[str], nlp=None, sbert_model=None
) -> Optional[str]:
    """Simplified attribute detection using basic keyword matching."""
    if not clause_text or not clause_text.strip():
        return None

    for attr_name in attribute_names:
        if validate_contextual_match(clause_text, attr_name, sbert_model):
            return f"{attr_name} (keyword)"

    return None

class SimilarityEngines:
    def __init__(self, sbert_model_name: str, use_cross_encoder: bool, cross_encoder_name: str):
        self.sbert = SentenceTransformer(sbert_model_name)
        self.use_cross_encoder = use_cross_encoder
        self.cross_encoder = None
        self.ce_tokenizer = None
        if use_cross_encoder:
            self.cross_encoder = AutoModelForSequenceClassification.from_pretrained(cross_encoder_name)
            self.ce_tokenizer = AutoTokenizer.from_pretrained(cross_encoder_name)
            self.cross_encoder.eval()

    @torch.no_grad()
    def sbert_score(self, a: str, b: str) -> float:
        embs = self.sbert.encode([a, b], convert_to_tensor=True, normalize_embeddings=True)
        sim = sbert_util.cos_sim(embs[0], embs[1]).item()
        return float(sim)

    @torch.no_grad()
    def cross_encoder_score(self, a: str, b: str) -> Optional[float]:
        if not self.use_cross_encoder or self.cross_encoder is None:
            return None
        inputs = self.ce_tokenizer(a, b, return_tensors="pt", truncation=True, padding=True, max_length=512)
        logits = self.cross_encoder(**inputs).logits
        if logits.shape[-1] == 3:
            probs = torch.softmax(logits, dim=-1).squeeze(0)
            entail = probs[-1].item()  # assume index 2 is 'entailment'
            return float(entail)
        return torch.sigmoid(logits).mean().item()


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

def check_placeholder_substitution(clause_text: str, template_text: str) -> bool:
    """Check if differences are only due to placeholder/value substitutions."""
    def normalize_placeholders(text):
        text = re.sub(r'\b\d+(\.\d+)?%?\b', '[NUMBER]', text)
        text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', '[DATE]', text)
        text = re.sub(r'\$\d+(\.\d+)?\b', '[AMOUNT]', text)
        text = re.sub(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', '[MONTH]', text, flags=re.IGNORECASE)
        return text.lower().strip()
    
    normalized_clause = normalize_placeholders(clause_text)
    normalized_template = normalize_placeholders(template_text)
    
    similarity = fuzz.ratio(normalized_clause, normalized_template)
    return similarity >= 85

def check_key_verbs_preserved(clause_text: str, template_text: str, nlp) -> bool:
    """Check if key verbs and objects are preserved despite wording changes."""
    if not nlp:
        return False
    
    clause_doc = nlp(clause_text)
    template_doc = nlp(template_text)
    
    def extract_key_elements(doc):
        elements = set()
        for token in doc:
            if token.pos_ == 'VERB' and not token.is_stop:
                elements.add(token.lemma_.lower())
            if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                elements.add(token.lemma_.lower())
        return elements
    
    clause_elements = extract_key_elements(clause_doc)
    template_elements = extract_key_elements(template_doc)
    
    if not template_elements:
        return False
    
    overlap = len(clause_elements.intersection(template_elements))
    return overlap / len(template_elements) >= 0.7

def detect_methodology_reference(clause_text: str) -> bool:
    """Detect references to different payment methodologies."""
    methodology_patterns = [
        r'\bmedicare\s+(fee\s+schedule|rates?)\b',
        r'\bbilled\s+charges?\b',
        r'\busual\s+and\s+customary\b',
        r'\bfair\s+market\s+value\b',
        r'\bprevailing\s+rates?\b',
        r'\bother\s+payer\s+rates?\b',
        r'\balternate\s+payment\b',
        r'\bdifferent\s+methodology\b'
    ]
    
    clause_lower = clause_text.lower()
    return any(re.search(pattern, clause_lower) for pattern in methodology_patterns)

def classify_against_template(clause, template: TemplateClause, engines: SimilarityEngines) -> Tuple[str, float, str, List[StepResult]]:
    steps = []
    c_raw, c_norm = clause["text"], clause.get("norm", clause["text"].lower())
    t_norm = template.norm_text

    has_exc = contains_exception_tokens(c_raw, template_has_exception=template.has_exception_tokens)
    steps.append(StepResult("exception_check", has_exc, None, "Detected conditional/exception tokens in clause; template lacks them."))
    if has_exc:
        return "Non-Standard", 0.90, "new_condition", steps

    exact = (c_norm == t_norm)
    steps.append(StepResult("exact_normalized_match", exact, None, "Clause equals template after normalization."))
    if exact:
        return "Standard", 0.99, "exact_norm", steps

    placeholder_match = check_placeholder_substitution(c_raw, template.raw_text)
    steps.append(StepResult("placeholder_substitution", placeholder_match, None, "Placeholders/value substitutions align (e.g., percent, dates)."))
    if placeholder_match:
        return "Standard", 0.95, "placeholder_subst", steps

    lex = fuzz.ratio(c_norm, t_norm)
    
    key_verbs_preserved = check_key_verbs_preserved(c_raw, template.raw_text, None)  # nlp passed separately if needed
    steps.append(StepResult("key_verbs_preserved", key_verbs_preserved, None, "Key verbs and objects preserved despite wording changes."))
    if key_verbs_preserved and lex >= 80:  # Lower threshold with verb preservation
        return "Standard", 0.88, "minor_wording_diff", steps
    steps.append(StepResult("fuzzy_lexical", lex >= FUZZY_THRESHOLD, float(lex)/100.0, f"RapidFuzz ratio={lex}"))
    if lex >= FUZZY_THRESHOLD:
        return "Standard", 0.90, "lexical_high", steps

    sbert_sim = engines.sbert_score(c_raw, template.raw_text)
    steps.append(StepResult("semantic_sbert", sbert_sim >= SBERT_THRESHOLD, sbert_sim, f"SBERT cosine={sbert_sim:.3f}"))
    if sbert_sim >= SBERT_THRESHOLD:
        return "Standard", 0.85, "semantic_high", steps

    if SBERT_AMBIG_LOW <= sbert_sim < SBERT_AMBIG_HIGH:
        steps.append(StepResult("semantic_ambiguous_band", True, sbert_sim, "SBERT score in ambiguous range; needs review."))
        return "Ambiguous", sbert_sim, "semantic_ambiguous", steps

    has_diff_methodology = detect_methodology_reference(c_raw)
    steps.append(StepResult("different_methodology", has_diff_methodology, None, "References alternate payment methodology (Medicare rates, billed charges, etc.)."))
    if has_diff_methodology:
        return "Non-Standard", 0.85, "different_methodology", steps
    if engines.use_cross_encoder:
        ce = engines.cross_encoder_score(c_raw, template.raw_text)
        steps.append(StepResult("deberta_cross_encoder", ce is not None and ce >= 0.7, ce, "Cross-encoder entailment prob (>=0.7 → Standard)."))
        if ce is not None and ce >= 0.7:
            return "Standard", float(ce), "deberta_ce_high", steps

    steps.append(StepResult("default_nonstandard", True, sbert_sim, "Low similarity and no earlier rule satisfied."))
    return "Non-Standard", float(sbert_sim), "low_similarity", steps

def choose_best_template(clause: Dict, templates: List[TemplateClause], engines: SimilarityEngines, target_attribute: str) -> Tuple[str, str, float, str, List[StepResult]]:
    """Choose the best matching template for a clause with a specific attribute."""
    matching_templates = [t for t in templates if t.attribute == target_attribute]
    
    if not matching_templates:
        return "No_Template", "Skip", 0.0, "no_template", []
    
    ranked = []
    for template in matching_templates:
        label, score, rule, steps = classify_against_template(clause, template, engines)
        tpl_name = template.name
        ranked.append((tpl_name, label, score, rule, steps))

    def score_key(x):
        tpl_name, label, score, rule, steps = x
        priority = {"Standard": 3, "Ambiguous": 2, "Non-Standard": 1}.get(label, 0)
        return (priority, score)

    tpl_name, label, score, rule, steps = sorted(ranked, key=score_key, reverse=True)[0]
    return tpl_name, label, score, rule, steps

def classify_clauses(clauses: List[Dict], attribute_names: List[str], templates: List[TemplateClause], engines: SimilarityEngines, nlp=None):
    decisions = []
    for cl in clauses:
        attr = detect_attribute_for_clause_spacy_regex(cl["text"], attribute_names, nlp, engines.sbert)

        if not attr:
            decisions.append(ClauseDecision(
                clause_id=cl["clause_id"], attribute=None, template_used=None,
                label="Skip", score=0.0, rule="no_target_attribute", steps=[], text=cl["text"]
            ))
            continue

        clean_attr = attr.split(' (')[0] if ' (' in attr else attr
        tpl_name, label, score, rule, steps = choose_best_template(cl, templates, engines, clean_attr)
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
    print("Starting Contract Clause Classifier...")
    
    print(f"Loaded attributes: {TARGET_ATTRIBUTES}")

    templates = load_templates(TEMPLATE_FILES)

    try:
        nlp = init_spacy(USE_SPACY_MODEL)
    except Exception as e:
        print("[WARN] spaCy init failed:", e)
        nlp = None

    engines = SimilarityEngines(
        sbert_model_name=USE_SBERT_MODEL,
        use_cross_encoder=USE_DEBERTA_CROSS_ENCODER,
        cross_encoder_name=DEBERTA_CE_MODEL
    )
    print("SBERT model loaded:", USE_SBERT_MODEL)
    print("DeBERTa CE enabled:", USE_DEBERTA_CROSS_ENCODER)

    print("Contract files:", CONTRACT_FILES)

    all_decisions = []
    for cpath in CONTRACT_FILES:
        if not Path(cpath).exists():
            print(f"[WARN] Contract file not found: {cpath}")
            continue
            
        if is_pdf(cpath):
            raw_text = pdf_to_text(cpath)
        else:
            raw_text = read_text_file(Path(cpath))
            
        print(f"{Path(cpath).name}: Extracted {len(split_into_clauses(raw_text))} clauses")
        clauses = split_into_clauses(raw_text)
        decisions = classify_clauses(clauses, TARGET_ATTRIBUTES, templates, engines, nlp)
        all_decisions.extend(decisions)

    df = pd.DataFrame(all_decisions)
    summary = df[df['label'] != 'Skip'].groupby(['attribute', 'label']).size().reset_index(name='count')
    print("Summary by attribute/label:")
    print(summary)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "clause_classification_summary.csv"
    out_json = OUT_DIR / "clause_classification_details.json"
    df.to_csv(out_csv, index=False)
    decisions_dict = [asdict(decision) for decision in all_decisions]
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(decisions_dict, f, ensure_ascii=False, indent=2)

    print(f"Saved summary CSV: {out_csv.resolve()}")
    print(f"Saved details JSON: {out_json.resolve()}")

    valid_df = df[df['label'].isin(['Standard', 'Non-Standard'])]
    print("Valid classified clauses:")
    print(valid_df[['clause_id', 'attribute', 'template_used', 'label', 'score', 'rule', 'text']])

    return df, all_decisions

if __name__ == "__main__":
    df, decisions = main()
