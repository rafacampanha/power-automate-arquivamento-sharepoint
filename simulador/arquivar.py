"""Simula localmente a regra do fluxo: move arquivos não modificados há N anos para um arquivo morto.

Por padrão só lista (dry-run). Use --executar para mover de fato. Gera log.csv no destino.
"""
from __future__ import annotations

import argparse
import csv
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class Candidato:
    origem: Path
    destino: Path
    modificado: datetime
    tamanho_mb: float


def data_corte(anos: int, hoje: datetime | None = None) -> datetime:
    return (hoje or datetime.now()) - timedelta(days=round(365.25 * anos))


def encontrar(origem: Path, destino: Path, anos: int, hoje: datetime | None = None) -> list[Candidato]:
    corte = data_corte(anos, hoje)
    saida = []
    for arq in sorted(p for p in origem.rglob("*") if p.is_file()):
        mod = datetime.fromtimestamp(arq.stat().st_mtime)
        if mod < corte:
            rel = arq.relative_to(origem)
            saida.append(Candidato(arq, destino / str(mod.year) / rel, mod, arq.stat().st_size / 1_048_576))
    return saida


def executar(candidatos: list[Candidato], destino: Path, mover: bool) -> Path:
    destino.mkdir(parents=True, exist_ok=True)
    log = destino / "log.csv"
    with log.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if f.tell() == 0:
            w.writerow(["executado_em", "origem", "destino", "modificado", "tamanho_mb", "status"])
        for c in candidatos:
            status = "simulado"
            if mover:
                try:
                    c.destino.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(c.origem, c.destino)               # 1) copia
                    if c.destino.stat().st_size == c.origem.stat().st_size:
                        c.origem.unlink()                            # 2) só exclui se a cópia confere
                        status = "movido"
                    else:
                        status = "erro: tamanho diferente"
                except OSError as e:
                    status = f"erro: {e}"
            w.writerow([datetime.now().isoformat(timespec="seconds"), c.origem, c.destino,
                        c.modificado.date(), f"{c.tamanho_mb:.2f}", status])
    return log


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("origem", type=Path)
    p.add_argument("destino", type=Path)
    p.add_argument("--anos", type=int, default=5)
    p.add_argument("--executar", action="store_true", help="move de fato (sem isso é só simulação)")
    a = p.parse_args()
    cands = encontrar(a.origem, a.destino, a.anos)
    for c in cands:
        print(f"{c.modificado:%Y-%m-%d}  {c.tamanho_mb:8.2f} MB  {c.origem}")
    print(f"\n{len(cands)} arquivo(s), {sum(c.tamanho_mb for c in cands):.2f} MB")
    if cands:
        print("log:", executar(cands, a.destino, a.executar))


if __name__ == "__main__":
    main()
