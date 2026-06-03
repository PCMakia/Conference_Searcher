"""CCF subfield to WikiCFP category and CCF-deadlines sub-field mapping."""

TOPIC_CHOICES = [
    "All Computer Science",
    "Artificial Intelligence",
    "Machine Learning",
    "Computer Vision",
    "Natural Language Processing",
    "Data Mining",
    "Databases",
    "Software Engineering",
    "Security",
    "Networking",
    "Human-Computer Interaction",
    "Robotics",
    "Theory",
]

TOPIC_TO_WIKICFP: dict[str, str] = {
    "All Computer Science": "computer science",
    "Artificial Intelligence": "artificial intelligence",
    "Machine Learning": "machine learning",
    "Computer Vision": "computer vision",
    "Natural Language Processing": "natural language processing",
    "Data Mining": "data mining",
    "Databases": "database",
    "Software Engineering": "software engineering",
    "Security": "security",
    "Networking": "networking",
    "Human-Computer Interaction": "human computer interaction",
    "Robotics": "robotics",
    "Theory": "theory",
}

# CCF-deadlines `sub` codes (see ccfddl/ccf-deadlines)
TOPIC_TO_CCF_SUB: dict[str, set[str]] = {
    "All Computer Science": {"ALL"},
    "Artificial Intelligence": {"AI"},
    "Machine Learning": {"AI"},
    "Computer Vision": {"CV"},
    "Natural Language Processing": {"NLP"},
    "Data Mining": {"DM", "DB"},
    "Databases": {"DB"},
    "Software Engineering": {"SE"},
    "Security": {"SC"},
    "Networking": {"NW"},
    "Human-Computer Interaction": {"HC"},
    "Robotics": {"RO"},
    "Theory": {"TH"},
}


def wikicfp_category(topic: str) -> str:
    return TOPIC_TO_WIKICFP.get(topic, "computer science")


def web_search_query(topic: str, semantic_query: str = "") -> str:
    """Build a web search query biased toward US conference CFP pages."""
    from datetime import date

    year = date.today().year
    parts: list[str] = []
    if semantic_query.strip():
        parts.append(semantic_query.strip())
    parts.append(topic)
    parts.append("conference USA call for papers")
    parts.append(str(year))
    parts.append(str(year + 1))
    return " ".join(parts)
