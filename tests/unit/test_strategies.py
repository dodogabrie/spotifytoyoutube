from core.matching.strategies import ytmusic_queries
from core.models import NormalizedTrack


def test_isrc_query_first_when_available():
    t = NormalizedTrack(
        source_id="1",
        title="Wonderwall",
        artists=["Oasis"],
        isrc="GBARL9500001",
    )
    qs = ytmusic_queries(t)
    assert qs[0] == "GBARL9500001"
    assert any("Wonderwall" in q for q in qs)


def test_normalized_title_fallback_when_different():
    t = NormalizedTrack(
        source_id="1",
        title="Wonderwall (feat. Liam)",
        artists=["Oasis"],
    )
    qs = ytmusic_queries(t)
    assert any("(feat" in q for q in qs)
    assert any("wonderwall" in q.lower() and "(feat" not in q.lower() for q in qs)


def test_no_duplicate_queries():
    t = NormalizedTrack(source_id="1", title="Plain Title", artists=["Artist"])
    qs = ytmusic_queries(t)
    assert len(qs) == len({q.lower() for q in qs})
