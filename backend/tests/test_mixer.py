from app.feed.mixer import Candidate, mix, slot_for


def pool(n, kind, artists=None, genre="pop"):
    return [Candidate(f"{kind}{i}", f"art{i % (artists or n)}{kind}", (genre,), kind, 1 - i / 1000) for i in range(n)]


def test_slot_pattern_gives_40_10_in_every_window():
    slots = [slot_for(i) for i in range(500)]
    for s in range(0, 450):
        w = slots[s:s + 50]
        assert w.count("discovery") == 10 and w.count("popular") == 40


def test_mix_respects_ratio_no_repeats_and_artist_gap():
    out = mix(pool(80, "popular", artists=20), pool(30, "discovery", artists=10), 0, 50, [], "sess")
    assert len(out) == 50
    assert sum(p.slot == "discovery" for p in out) == 10
    ids = [p.candidate.track_id for p in out]
    assert len(ids) == len(set(ids))
    for i in range(1, len(out)):
        prev = {p.candidate.artist_id for p in out[max(0, i - 3):i]}
        assert out[i].candidate.artist_id not in prev


def test_tolerance_when_discovery_pool_empty():
    out = mix(pool(10, "popular"), [], 0, 10, [], "s")
    assert len(out) == 10
    assert [p.tolerance for p in out if p.planned == "discovery"] == [True, True]


def test_genre_not_more_than_two_in_a_row_when_alternatives_exist():
    pops = pool(30, "popular", genre="pop") + [Candidate(f"r{i}", f"ra{i}", ("rap",), "popular", 0.1) for i in range(30)]
    out = mix(pops, [], 0, 12, [], "s")
    g = [p.candidate.genres[0] for p in out]
    assert all(not (g[i] == g[i - 1] == g[i - 2]) for i in range(2, len(g)))


def test_affinity_and_penalty_shift_odds_but_keep_variety():
    a = Candidate("a", "x", ("pop",), "popular", 0.5)
    b = Candidate("b", "y", ("rap",), "popular", 0.5, affinity=0.4)
    c = Candidate("c", "z", ("rock",), "popular", 0.5, penalty=0.45)
    firsts = [mix([a, b, c], [], 0, 1, [], f"s{i}")[0].candidate.track_id for i in range(600)]
    assert firsts.count("b") > firsts.count("a") > firsts.count("c") > 0


def test_first_card_changes_between_sessions():
    pops = pool(100, "popular", artists=40)
    firsts = {mix(pops, [], 0, 1, [], f"sessione-{i}")[0].candidate.track_id for i in range(30)}
    assert len(firsts) >= 10  # prima: sempre lo stesso brano in cima
