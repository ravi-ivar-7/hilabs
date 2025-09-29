"""
Classification parameters and constants for healthcare contract analysis.
Centralized configuration for thresholds, patterns, and classification settings.
"""

# Target attributes for healthcare contract analysis
TARGET_ATTRIBUTES = [
    "Medicaid Timely Filing",
    "Medicare Timely Filing", 
    "No Steerage/SOC",
    "Medicaid Fee Schedule",
    "Medicare Fee Schedule"
]

# Exception tokens that indicate non-standard clauses
EXCEPTION_TOKENS = [
    'except', 'unless', 'provided that',
    'subject to', 'however,', 'save that',
    'notwithstanding', 'only if'
]

# Placeholder normalization patterns
PLACEHOLDER_MAP = {
    # Percentages (XX%, 100%, 95% etc.)
    r"\[\(?\s*XX\s*%\s*\)?\]": "<PCT>",                # generic percentage placeholder
    r"\b\d{1,3}\s*%\b": "<PCT>",                       # numeric percentages like 100%, 95%
    r"\b(one\s*hundred|ninety[-\s]*five|fifty)\s*percent\b": "<PCT>",

    # Compensation / Fee references
    r"\b(Fee\s+Schedule|Compensation\s+Schedule|Plan\s+Compensation\s+Schedule|WCS|PCS)\b": "<FEE_SCHEDULE>",
    r"\b(Rate|Eligible\s+Charge[s]?)\b": "<RATE>",

    # Parties / Organization
    r"\b(Plan|Company|Network|Agency|Affiliate|Other\s+Payors?)\b": "<ORG>",
    r"\b(Provider|Participating\s+Provider)\b": "<PROVIDER>",

    # Members
    r"\b(Member|Enrollee|Subscriber|Insured|Beneficiary|Covered\s+(Person|Individual)|Dependent)\b": "<MEMBER>",

    # Programs
    r"\b(Government\s+Program|Medicare|Medicaid|CMS|HCA)\b": "<GOV_PROGRAM>",

    # Documents
    r"\b(Participation\s+Attachment[s]?)\b": "<ATTACHMENT>",
    r"\b(provider\s+manual\(s\))\b": "<PROVIDER_MANUAL>",
    r"\b(Health\s+Benefit\s+Plan)\b": "<PLAN_DOC>",

    # Payments
    r"\b(Cost\s*Share[s]?|copayment[s]?|coinsurance|deductible[s]?)\b": "<COST_SHARE>",
    r"\b(Claim[s]?)\b": "<CLAIM>",

    # Legal placeholders
    r"\b(Regulatory\s+Requirements?)\b": "<REG_REQ>",
    r"\b(Effective\s+Date|MM/DD/YYYY)\b": "<DATE>",
    r"\[\s*_{2,}\s*\]": "<BLANK>",   # underscores for blanks like [_________]

    # Misc
    r"\b(Health\s+Services?|Covered\s+Services?)\b": "<SERVICE>",
    r"\b(Medically\s+Necessary|Medical\s+Necessity)\b": "<MEDICAL_NECESSITY>",
}

# Classification thresholds
FUZZY_THRESHOLD = 70  # RapidFuzz similarity threshold for string matching
SBERT_THRESHOLD = 0.60  # SBERT semantic similarity threshold for standard classification
SBERT_AMBIG_LOW = 0.50  # Lower bound for ambiguous classification
SBERT_AMBIG_HIGH = 0.70  # Upper bound for ambiguous classification

ATTRIBUTE_PATTERNS = {
    "Medicaid Timely Filing": [
        r"submit.*claims.*\d+.*days?", 
        r"timely.*filing", 
        r"filing.*deadline",
        r"claims.*rendered.*refuse payment", 
        r"secondary payor.*\d+.*days?"
    ],
    "Medicare Timely Filing": [
        r"submit.*claims.*\d+.*days?", 
        r"timely.*filing", 
        r"filing.*deadline", 
        r"claims.*rendered.*refuse payment", 
        r"secondary payor.*\d+.*days?"
    ],
    "No Steerage/SOC": [
        r"eligible.*participate.*networks", 
        r"provider networks attachment",
        r"steerage", 
        r"standard.*care", 
        r"soc", 
        r"steering"
    ],
    "Medicaid Fee Schedule": [
        r"eligible charges.*covered services", 
        r"compensation schedule",
        r"\d+.*percent.*eligible charges", 
        r"cost shares", 
        r"payment.*full"
    ],
    "Medicare Fee Schedule": [
        r"medicare advantage network", 
        r"ma covered services", 
        r"ma members",
        r"related entity", 
        r"common ownership.*control", 
        r"management functions"
    ]
}

# Classification confidence scores
CONFIDENCE_SCORES = {
    "exact_match": 99,
    "placeholder_match": 95,
    "fuzzy_match": 90,
    "semantic_match": 85,
    "exception_detected": 90,
    "methodology_detected": 85
}

# Template clauses extracted from actual PDFs
TN_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility",
    "Medicare Timely Filing": "Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility. 3.1.1 In situations of enrollment in with a retroactive eligibility date, the time frames for filing a claim shall begin on the date that receives notification from of the Medicaid Member's eligibility/enrollment.",
    "No Steerage/SOC": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment",
    "Medicaid Fee Schedule": "one hundred percent (100%) of Eligible Charges for Covered Services, or the total reimbursement amount that Provider and have agreed upon as set forth in the Compensation Schedule. The Rate includes applicable Cost Shares, and shall represent payment in full to Provider for Covered Services.",
    "Medicare Fee Schedule": "Medicare Advantage Network means Network of Providers that provides MA Covered Services to MA Members. Related Entity(ies) means any entity that is related to by common ownership or control and performs some of management functions under contract or delegation."
}

WA_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "Unless otherwise instructed, or required by Regulatory Requirements, Provider shall submit Claims for Medicaid Claims.",
    "Medicare Timely Filing": "Provider shall submit Claims to Plan, using appropriate and current Coded Service Identifier(s), within three hundred sixty-five (365) days from the date the Health Services are rendered or Plan may refuse payment. If Plan is the secondary payor, the three hundred sixty-five (365) day period will not begin until Provider receives notification of primary payor's responsibility.",
    "No Steerage/SOC": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment of this Agreement",
    "Medicaid Fee Schedule": "one hundred percent (100%) of Eligible Charges for Covered Services, or the total reimbursement amount that Provider and have agreed upon as set forth in the Compensation Schedule. The Rate includes applicable Cost Shares, and shall represent payment in full to Provider for Covered Services.",
    "Medicare Fee Schedule": "As a participant in Plan's Medicare Advantage Network, Provider will render MA Covered Services to MA Members enrolled in Plan's Medicare Advantage Program in accordance with the terms and conditions of the Agreement."
}

# Processing settings
MAX_CLAUSE_LENGTH = 5000  # Maximum characters per clause
MIN_CLAUSE_LENGTH = 10    # Minimum characters per clause
BATCH_SIZE = 50           # Number of clauses to process in batch
