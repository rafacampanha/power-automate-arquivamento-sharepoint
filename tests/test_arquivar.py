import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "simulador"))
from arquivar import encontrar, executar  # noqa: E402


def _criar(p: Path, quando: datetime):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")
    ts = quando.timestamp()
    os.utime(p, (ts, ts))


def test_move_so_os_antigos(tmp_path):
    origem, destino = tmp_path / "sp", tmp_path / "morto"
    _criar(origem / "contratos" / "velho.pdf", datetime(2018, 3, 1))
    _criar(origem / "novo.xlsx", datetime(2026, 1, 1))
    cands = encontrar(origem, destino, 5, hoje=datetime(2026, 11, 15))
    assert [c.origem.name for c in cands] == ["velho.pdf"]
    assert cands[0].destino == destino / "2018" / "contratos" / "velho.pdf"

    executar(cands, destino, mover=True)
    assert not (origem / "contratos" / "velho.pdf").exists()
    assert (destino / "2018" / "contratos" / "velho.pdf").exists()
    assert "movido" in (destino / "log.csv").read_text()


def test_dry_run_nao_mexe(tmp_path):
    origem, destino = tmp_path / "sp", tmp_path / "morto"
    _criar(origem / "a.txt", datetime(2015, 1, 1))
    executar(encontrar(origem, destino, 5), destino, mover=False)
    assert (origem / "a.txt").exists()
    assert "simulado" in (destino / "log.csv").read_text()
