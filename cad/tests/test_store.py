"""The part store hands back the same solid it built, and builds again when
its files go missing."""

import shutil

from build123d import Box

from handful_cad import store


def test_store_round_trips_and_rebuilds_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "ROOT", tmp_path)
    monkeypatch.setenv("HANDFUL_CACHE", "1")
    calls = []

    def block(size: float, height: float = 2.0):
        calls.append(size)
        return Box(size, size, height)

    first = store.stored(block)
    built = first(3.0)
    assert first.is_stored(3.0, height=2.0)
    assert store.path_for("block", (3.0, 2.0)).exists()

    loaded = store.stored(block)(size=3.0)
    assert calls == [3.0]
    assert abs(loaded.volume - built.volume) < 1e-9

    shutil.rmtree(tmp_path / store.SOURCE)
    again = store.stored(block)(3.0)
    assert calls == [3.0, 3.0]
    assert abs(again.volume - built.volume) < 1e-9


def test_store_can_be_switched_off(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "ROOT", tmp_path)
    monkeypatch.setenv("HANDFUL_CACHE", "0")
    store.stored(lambda: Box(1, 1, 1))()
    assert not any(tmp_path.iterdir())
