from core.matching.normalize import normalize_artist, normalize_title


def test_strips_feat_parenthetical():
    assert normalize_title("Song Name (feat. Artist X)") == "song name"


def test_strips_remaster_tag_after_dash():
    assert normalize_title("Black Dog - Remaster") == "black dog"
    assert normalize_title("Black Dog - Remastered 2007") == "black dog"


def test_strips_accents_and_lowercases():
    assert normalize_title("Café del Mar") == "cafe del mar"


def test_squashes_whitespace():
    assert normalize_title("  Hello    World  ") == "hello world"


def test_artist_normalization():
    assert normalize_artist("Beyoncé") == "beyonce"
    assert normalize_artist("  AC/DC  ") == "ac/dc"
