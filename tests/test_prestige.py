import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import Conference
from src.ranking.prestige import PrestigeRanker


def test_ranking_order():
    ranker = PrestigeRanker()
    confs = [
        Conference(name="Unknown Workshop", acronym="UNK", location="Boston, MA, USA"),
        Conference(name="CVPR 2026", acronym="CVPR", location="Denver, CO, USA"),
        Conference(name="NeurIPS 2025", acronym="NeurIPS", location="San Diego, CA, USA"),
    ]
    ranked = ranker.rank(confs)
    assert ranked[0].acronym in ("CVPR", "NeurIPS")
    assert ranked[0].prestige_score >= ranked[-1].prestige_score
