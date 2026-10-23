"""Sample documents for batch ingestion and metadata filtering."""

SAMPLE_DOCUMENTS = [
    {
        "text": (
            "The non-disclosure agreement restricts disclosure of confidential "
            "client information for two years after the contract ends."
        ),
        "category": "legal",
        "author": "Alice Chen",
    },
    {
        "text": (
            "This service agreement defines payment terms, liability limits, "
            "and termination conditions for the vendor relationship."
        ),
        "category": "legal",
        "author": "Marcus Hale",
    },
    {
        "text": (
            "New hires complete orientation, benefits enrollment, and a "
            "90-day performance review with their manager."
        ),
        "category": "hr",
        "author": "Priya Shah",
    },
    {
        "text": (
            "The remote-work policy requires core hours from 10:00 to 15:00 "
            "and a written equipment agreement."
        ),
        "category": "hr",
        "author": "Diego Morales",
    },
    {
        "text": (
            "Third-quarter operating expenses exceeded the forecast by 4 percent, "
            "driven by cloud infrastructure and contractor fees."
        ),
        "category": "finance",
        "author": "Elena Rossi",
    },
]
