"""Synthetic sample search queries, results, and factual claims for SearchEval."""

from __future__ import annotations

from typing import Any

from src.evaluator.pipeline import evaluate_search_session

SYNTHETIC_SAMPLE_NOTICE = (
    "All sample queries, URLs (*.invalid / example.*), snippets, and claims below are "
    "clearly labeled synthetic training examples created for evaluation workflow practice."
)

SAMPLE_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "edu-python-comprehensions",
        "category": "Educational Information",
        "query": "how do python list comprehensions work with conditions",
        "results": [
            {
                "title": "Python List Comprehensions with Conditional Filtering: Step-by-Step Guide",
                "url": "https://docs.python-learning.example.edu/guides/list-comprehensions",
                "source_name": "Open Python Learning Lab (Synthetic)",
                "author": "Dr. Maya Patel",
                "published_date": "2025-09-12",
                "supporting_evidence": "Synthetic educational module covering syntax [expr for item in iterable if cond] and readability trade-offs.",
                "reference_urls": ["https://docs.python-learning.example.edu/curriculum/syllabus"],
                "description": (
                    "This guide explains how Python list comprehensions work with conditional if-clauses "
                    "to filter items cleanly. It covers syntax examples, nested conditions, and when a standard "
                    "for-loop improves readability over complex one-liners."
                ),
            },
            {
                "title": "10 Shocking Secret Tricks to Write Python Fast",
                "url": "https://fast-code-blog.example.com/python-tricks",
                "source_name": "Fast Code Blog (Synthetic)",
                "author": "",
                "published_date": "",
                "supporting_evidence": "",
                "description": "You won't believe these Python secret trick tips. Click here now for Python code.",
            },
            {
                "title": "For Loops and Iteration Basics in Python 3",
                "url": "https://intro-cs.example.org/python/for-loops",
                "source_name": "Intro CS Archive (Synthetic)",
                "author": "Curriculum Committee",
                "published_date": "2024-03-18",
                "supporting_evidence": "Covers standard loop constructs without focusing specifically on comprehension syntax.",
                "description": (
                    "An overview of standard for-loops, range iteration, and conditional branching in Python 3. "
                    "Includes basic exercises for introductory programming students."
                ),
            },
        ],
        "claims": [
            {
                "claim_id": "sample-c1",
                "claim_text": "List comprehensions support a trailing if-clause to filter elements during iteration.",
                "supporting_evidence": "Confirmed in synthetic Python grammar reference section 5.1.3.",
                "source_urls": ["https://docs.python-learning.example.edu/curriculum/syllabus"],
                "status": "Supported",
                "reviewer_notes": "Verified against synthetic language reference.",
                "result_title": "Python List Comprehensions with Conditional Filtering: Step-by-Step Guide",
            }
        ],
    },
    {
        "id": "edu-photosynthesis",
        "category": "Educational Information",
        "query": "photosynthesis light dependent reactions overview",
        "results": [
            {
                "title": "Photosynthesis Overview: Light-Dependent Reactions and Calvin Cycle",
                "url": "https://biology-open.example.edu/cellular-energy/photosynthesis",
                "source_name": "Open Biology Textbooks (Synthetic)",
                "author": "Prof. Alan Brooks",
                "published_date": "2025-05-04",
                "supporting_evidence": "Describes thylakoid membrane electron transport, ATP synthesis, and NADPH generation.",
                "reference_urls": ["https://biology-open.example.edu/references/plant-physiology"],
                "description": (
                    "Explains how light-dependent reactions occur in chloroplast thylakoid membranes, "
                    "converting light energy into ATP and NADPH while splitting water molecules and releasing oxygen."
                ),
            },
            {
                "title": "Plant Care Guide for Indoor Succulents",
                "url": "https://garden-notes.example.com/succulents-light",
                "source_name": "Garden Notes (Synthetic)",
                "author": "L. Gomez",
                "published_date": "2025-02-10",
                "supporting_evidence": "",
                "description": (
                    "Covers window placement, watering schedules, and sunlight exposure for indoor succulents "
                    "and low-light houseplants."
                ),
            },
        ],
        "claims": [
            {
                "claim_id": "sample-c2",
                "claim_text": "Light-dependent reactions take place in the thylakoid membranes of chloroplasts.",
                "supporting_evidence": "Synthetic biology textbook Chapter 8 diagram and text explicitly locate Photosystems I and II in thylakoid membranes.",
                "source_urls": ["https://biology-open.example.edu/references/plant-physiology"],
                "status": "Supported",
                "reviewer_notes": "Standard foundational biology concept backed by synthetic text.",
                "result_title": "Photosynthesis Overview: Light-Dependent Reactions and Calvin Cycle",
            }
        ],
    },
    {
        "id": "tech-tls13",
        "category": "Technology",
        "query": "TLS 1.3 handshake steps and security improvements",
        "results": [
            {
                "title": "TLS 1.3 Handshake Explained: 1-RTT Key Exchange and Security Upgrades",
                "url": "https://netsec-handbook.example.org/protocols/tls-1-3-handshake",
                "source_name": "Network Security Handbook (Synthetic)",
                "author": "Security Engineering Group",
                "published_date": "2025-11-01",
                "supporting_evidence": "Compares 1-RTT handshake latency and removal of legacy RSA static key exchange.",
                "reference_urls": ["https://netsec-handbook.example.org/specs/tls13-summary"],
                "description": (
                    "Details the TLS 1.3 handshake sequence, showing how Ephemeral Diffie-Hellman key exchange "
                    "achieves 1-RTT setup, enforces forward secrecy, and removes deprecated cipher suites."
                ),
            },
            {
                "title": "What Is HTTPS? Basic Encryption Overview",
                "url": "https://web-basics.example.com/https-overview",
                "source_name": "Web Basics Hub (Synthetic)",
                "author": "Editorial Staff",
                "published_date": "2021-06-15",
                "supporting_evidence": "",
                "description": (
                    "A short beginner summary of HTTPS certificates and browser padlocks without protocol-level "
                    "details on TLS 1.2 or TLS 1.3 handshakes."
                ),
            },
        ],
        "claims": [
            {
                "claim_id": "sample-c3",
                "claim_text": "TLS 1.3 supports a 1-RTT full handshake compared to 2-RTT in earlier versions.",
                "supporting_evidence": "Synthetic protocol summary documents ClientHello with key_share reducing round trips to 1-RTT.",
                "source_urls": ["https://netsec-handbook.example.org/specs/tls13-summary"],
                "status": "Supported",
                "reviewer_notes": "Supported by synthetic spec reference.",
                "result_title": "TLS 1.3 Handshake Explained: 1-RTT Key Exchange and Security Upgrades",
            }
        ],
    },
    {
        "id": "tech-rest-graphql",
        "category": "Technology",
        "query": "compare REST vs GraphQL API performance and caching",
        "results": [
            {
                "title": "REST vs GraphQL Comparison: Caching, Over-Fetching, and Latency Trade-Offs",
                "url": "https://api-architecture.example.com/rest-vs-graphql",
                "source_name": "API Architecture Journal (Synthetic)",
                "author": "Priya Nair",
                "published_date": "2026-01-20",
                "supporting_evidence": "Includes HTTP CDN cache-control comparison and query-complexity analysis.",
                "reference_urls": ["https://api-architecture.example.com/benchmarks/2026-api-report"],
                "description": (
                    "Compares REST and GraphQL architectures across HTTP caching, payload size, over-fetching, "
                    "and backend resolver complexity to help engineering teams choose the right interface."
                ),
            },
            {
                "title": "REST API Tutorial for Beginners",
                "url": "https://dev-notes.example.net/rest-tutorial",
                "source_name": "Dev Notes (Synthetic)",
                "author": "",
                "published_date": "2023-08-09",
                "supporting_evidence": "",
                "description": "Covers HTTP GET and POST endpoints in REST APIs. Does not discuss GraphQL or caching.",
            },
        ],
        "claims": [],
    },
    {
        "id": "tech-vector-search",
        "category": "Technology",
        "query": "hybrid search TF-IDF keyword and semantic vector ranking",
        "results": [
            {
                "title": "Hybrid Search Architecture: Combining Lexical TF-IDF with Vector Similarity",
                "url": "https://ir-engineering.example.org/articles/hybrid-search-ranking",
                "source_name": "Information Retrieval Engineering (Synthetic)",
                "author": "K. Chen",
                "published_date": "2026-03-14",
                "supporting_evidence": "Explains Reciprocal Rank Fusion (RRF) for blending sparse and dense scores.",
                "reference_urls": ["https://ir-engineering.example.org/papers/rrf-notes"],
                "description": (
                    "Explains how hybrid search pipelines blend exact lexical matching from TF-IDF or BM25 "
                    "with dense embeddings using reciprocal rank fusion to improve recall on technical queries."
                ),
            },
            {
                "title": "Keyword Ranking SEO Tool Pricing",
                "url": "https://seo-vendor.example.com/pricing",
                "source_name": "SEO Vendor (Synthetic)",
                "author": "",
                "published_date": "2025-12-01",
                "supporting_evidence": "",
                "description": "Compare monthly keyword ranking software plans and agency dashboard pricing.",
            },
        ],
        "claims": [],
    },
    {
        "id": "health-flu-prevention",
        "category": "Health Information",
        "query": "seasonal influenza prevention guidelines handwashing vaccination",
        "results": [
            {
                "title": "Seasonal Influenza Prevention Guidelines: Vaccination and Hygiene Practices",
                "url": "https://public-health-synth.example.org/flu/prevention-guidelines",
                "source_name": "Synthetic Public Health Reference",
                "author": "Clinical Advisory Board (Synthetic)",
                "published_date": "2025-10-05",
                "supporting_evidence": "Summarizes annual immunization timing, respiratory etiquette, and hand hygiene.",
                "reference_urls": ["https://public-health-synth.example.org/flu/clinical-brief"],
                "description": (
                    "Outlines evidence-informed seasonal flu prevention steps including annual vaccination, "
                    "frequent handwashing with soap, staying home when symptomatic, and ventilation practices."
                ),
            },
            {
                "title": "Miracle Cure Herbal Tea Stops All Flu Viruses Overnight!",
                "url": "http://miracle-health-promo.invalid/flu-cure",
                "source_name": "Unknown",
                "author": "",
                "published_date": "",
                "supporting_evidence": "",
                "description": (
                    "Miracle cure! Doctors hate this secret trick. 100% guaranteed instant immunity without vaccines."
                ),
            },
        ],
        "claims": [
            {
                "claim_id": "sample-c4",
                "claim_text": "Herbal tea provides 100% guaranteed instant immunity against all influenza strains.",
                "supporting_evidence": "Contradicted by synthetic clinical brief stating no beverage confers universal viral immunity.",
                "source_urls": ["https://public-health-synth.example.org/flu/clinical-brief"],
                "status": "Contradicted",
                "reviewer_notes": "Unsupported sensational health claim flagged as contradicted.",
                "result_title": "Miracle Cure Herbal Tea Stops All Flu Viruses Overnight!",
            }
        ],
    },
    {
        "id": "health-diabetes-nutrition",
        "category": "Health Information",
        "query": "type 2 diabetes balanced nutrition fiber glycemic index basics",
        "results": [
            {
                "title": "Nutrition Basics for Type 2 Diabetes: Dietary Fiber and Carbohydrate Balance",
                "url": "https://metabolic-care.example.edu/patient-guides/diabetes-nutrition",
                "source_name": "Synthetic Metabolic Care Institute",
                "author": "R. Alvarez, RD",
                "published_date": "2025-07-22",
                "supporting_evidence": "Reviews non-starchy vegetables, whole grains, fiber intake, and meal consistency.",
                "reference_urls": ["https://metabolic-care.example.edu/references/dietary-standards"],
                "description": (
                    "Covers practical nutrition principles for managing Type 2 diabetes, including emphasizing "
                    "high-fiber whole foods, moderating refined carbohydrates, and understanding glycemic load."
                ),
            },
            {
                "title": "Low-Carb Diet Recipe Collection",
                "url": "https://home-kitchen.example.com/low-carb-recipes",
                "source_name": "Home Kitchen Blog (Synthetic)",
                "author": "Chef Dan",
                "published_date": "2024-11-11",
                "supporting_evidence": "",
                "description": "Collection of 25 dinner recipes featuring roasted vegetables and grilled proteins.",
            },
        ],
        "claims": [
            {
                "claim_id": "sample-c5",
                "claim_text": "Higher dietary fiber intake helps moderate post-meal blood glucose spikes.",
                "supporting_evidence": "",
                "source_urls": [],
                "status": "Unverified",
                "reviewer_notes": "Pending clinical citation attachment from reviewer.",
                "result_title": "Nutrition Basics for Type 2 Diabetes: Dietary Fiber and Carbohydrate Balance",
            }
        ],
    },
    {
        "id": "gov-fafsa-deadlines",
        "category": "Government Information",
        "query": "official federal student aid FAFSA application deadlines 2026",
        "results": [
            {
                "title": "2026-2027 Federal Student Aid (FAFSA) Application Portal & Deadlines",
                "url": "https://student-aid-synth.example.gov/fafsa/2026-deadlines",
                "source_name": "Federal Student Aid Synthetic Portal",
                "author": "Office of Aid Administration (Synthetic)",
                "published_date": "2026-01-08",
                "supporting_evidence": "Lists federal submission cutoff, state priority dates, and correction windows.",
                "reference_urls": ["https://student-aid-synth.example.gov/fafsa/policy-notice"],
                "description": (
                    "Official synthetic portal summarizing 2026 federal FAFSA submission deadlines, state-specific "
                    "priority dates, required tax documentation, and online application steps."
                ),
            },
            {
                "title": "Archived 2018 Financial Aid Bulletin",
                "url": "https://legacy-agency.example.gov/archive/2018-aid-bulletin",
                "source_name": "Legacy Government Archive (Synthetic)",
                "author": "",
                "published_date": "2018-02-14",
                "supporting_evidence": "",
                "description": (
                    "Historical 2018-2019 academic year aid announcement. Superseded by newer federal aid rules."
                ),
            },
        ],
        "claims": [],
    },
    {
        "id": "gov-small-business-tax",
        "category": "Government Information",
        "query": "small business quarterly estimated tax filing requirements",
        "results": [
            {
                "title": "Small Business Quarterly Estimated Tax Requirements and Payment Schedule",
                "url": "https://tax-guidance-synth.example.gov/business/estimated-taxes",
                "source_name": "Synthetic Revenue Service",
                "author": "Small Business Division (Synthetic)",
                "published_date": "2026-02-01",
                "supporting_evidence": "Details quarterly due dates, safe-harbor thresholds, and electronic filing options.",
                "reference_urls": ["https://tax-guidance-synth.example.gov/forms/1040-es-synth"],
                "description": (
                    "Explains quarterly estimated tax filing thresholds for sole proprietors, partnerships, "
                    "and small corporations, including quarterly payment deadlines and penalty exceptions."
                ),
            },
            {
                "title": "Business Accounting Software Comparison",
                "url": "https://saas-compare.example.com/accounting-tools",
                "source_name": "SaaS Compare (Synthetic)",
                "author": "Editorial Team",
                "published_date": "2025-09-30",
                "supporting_evidence": "",
                "description": "Compares bookkeeping software pricing and invoicing features for small teams.",
            },
        ],
        "claims": [],
    },
    {
        "id": "gov-passport-renewal",
        "category": "Government Information",
        "query": "passport renewal processing times and required documents",
        "results": [
            {
                "title": "Passport Renewal Checklist: Processing Times, Photos, and Required Forms",
                "url": "https://travel-docs-synth.example.gov/passports/renewal-guide",
                "source_name": "Synthetic Consular Services",
                "author": "Travel Documentation Office",
                "published_date": "2026-04-10",
                "supporting_evidence": "Provides routine vs expedited timelines and form eligibility requirements.",
                "reference_urls": ["https://travel-docs-synth.example.gov/passports/fee-schedule"],
                "description": (
                    "Details current routine and expedited passport renewal processing times, eligibility rules, "
                    "photo specifications, and required supporting identification documents."
                ),
            },
            {
                "title": "International Travel Packing Checklist",
                "url": "https://wander-tips.example.com/packing-checklist",
                "source_name": "Wander Tips (Synthetic)",
                "author": "T. Morgan",
                "published_date": "2025-06-19",
                "supporting_evidence": "",
                "description": "A travel blog checklist covering luggage, power adapters, and airport arrival tips.",
            },
        ],
        "claims": [],
    },
    {
        "id": "news-urban-heat",
        "category": "News & Current Events",
        "query": "2026 city urban heat island cool pavement tree canopy programs",
        "results": [
            {
                "title": "Cities Expand Cool Pavement and Tree Canopy Programs in 2026 Heat Plans",
                "url": "https://civic-news-synth.example.org/climate/2026-urban-heat-programs",
                "source_name": "Civic Metro Dispatch (Synthetic)",
                "author": "Elena Novak",
                "published_date": "2026-06-18",
                "supporting_evidence": "Cites municipal pilot measurements comparing shaded vs unshaded street surface temperatures.",
                "reference_urls": ["https://civic-news-synth.example.org/data/2026-heat-pilot"],
                "description": (
                    "Reports on 2026 municipal urban heat island mitigation programs combining reflective cool "
                    "pavement coatings with targeted neighborhood tree canopy planting."
                ),
            },
            {
                "title": "Summer Weekend Concert Schedule Announced",
                "url": "https://local-events.example.com/summer-concerts",
                "source_name": "Local Events Daily (Synthetic)",
                "author": "Arts Desk",
                "published_date": "2026-06-12",
                "supporting_evidence": "",
                "description": "Lists outdoor park concert dates and transit parking advisories for summer weekends.",
            },
        ],
        "claims": [],
    },
    {
        "id": "news-microgrid-resilience",
        "category": "News & Current Events",
        "query": "latest municipal renewable microgrid grid resilience updates 2026",
        "results": [
            {
                "title": "Municipalities Pilot Solar-Plus-Storage Microgrids for Critical Facilities in 2026",
                "url": "https://energy-wire-synth.example.org/grid/2026-municipal-microgrids",
                "source_name": "Regional Energy Wire (Synthetic)",
                "author": "David Okafor",
                "published_date": "2026-08-04",
                "supporting_evidence": "Summarizes hospital and transit microgrid islanding tests during peak load.",
                "reference_urls": ["https://energy-wire-synth.example.org/reports/microgrid-2026"],
                "description": (
                    "Covers 2026 municipal investments in solar-plus-battery microgrids designed to keep water "
                    "treatment plants, emergency shelters, and transit hubs powered during grid outages."
                ),
            },
            {
                "title": "Home Solar Panel Tax Credit Overview",
                "url": "https://residential-solar.example.com/credits",
                "source_name": "Residential Solar Guide (Synthetic)",
                "author": "",
                "published_date": "2024-04-20",
                "supporting_evidence": "",
                "description": "General guide for homeowners evaluating rooftop solar panel installation costs.",
            },
        ],
        "claims": [],
    },
]


def get_sample_scenarios() -> list[dict[str, Any]]:
    """Return all synthetic sample scenarios."""
    return SAMPLE_SCENARIOS


def get_scenario_by_id(scenario_id: str) -> dict[str, Any] | None:
    """Look up a synthetic sample scenario by ID."""
    for item in SAMPLE_SCENARIOS:
        if item["id"] == scenario_id:
            return item
    return None


def build_sample_evaluations(limit: int = 4) -> list[dict[str, Any]]:
    """Generate evaluated records from the top synthetic sample scenarios."""
    records: list[dict[str, Any]] = []
    for scenario in SAMPLE_SCENARIOS[:limit]:
        record = evaluate_search_session(
            query=scenario["query"],
            results=scenario["results"],
            claims=scenario.get("claims", []),
            category=scenario["category"],
            reviewer_name="Sample Assessor",
            session_notes=f"Synthetic sample scenario ({scenario['id']}).",
            is_synthetic=True,
            evaluation_id=f"sample-{scenario['id']}",
        )
        records.append(record)
    return records
