
import argparse, csv, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from formal.tree import Node
from .parser_es import analizar

SALIDA = os.path.join(os.path.dirname(__file__), "resultados", "arboles")


def _etiqueta(n: Node) -> str:
    return n.tipo if n.valor is None or n.valor == n.tipo else f"{n.tipo}\n{n.valor}"


def _layout(n: Node, prof=0, hojas=None, pos=None):
    """x: hojas equiespaciadas; padres centrados sobre sus hijos. y: profundidad."""
    if hojas is None:
        hojas, pos = [0], {}
    if not n.hijos:
        pos[id(n)] = (hojas[0], -prof)
        hojas[0] += 1
    else:
        for h in n.hijos:
            _layout(h, prof + 1, hojas, pos)
        xs = [pos[id(h)][0] for h in n.hijos]
        pos[id(n)] = (sum(xs) / len(xs), -prof)
    return pos


def _aristas(n: Node):
    for h in n.hijos:
        yield n, h
        yield from _aristas(h)


def _nodos(n: Node):
    yield n
    for h in n.hijos:
        yield from _nodos(h)


def dibujar(arbol: Node, ruta_png: str, titulo: str = ""):
    pos = _layout(arbol)
    ancho = max(6, (max(x for x, _ in pos.values()) + 1) * 1.1)
    alto = max(3, (-min(y for _, y in pos.values()) + 1) * 0.95)
    fig, ax = plt.subplots(figsize=(ancho, alto))
    for p, h in _aristas(arbol):
        (x1, y1), (x2, y2) = pos[id(p)], pos[id(h)]
        ax.plot([x1, x2], [y1, y2], color="#888", lw=1, zorder=1)
    for n in _nodos(arbol):
        x, y = pos[id(n)]
        hoja = not n.hijos
        ax.text(x, y, _etiqueta(n), ha="center", va="center", fontsize=9, zorder=2,
                bbox=dict(boxstyle="round,pad=0.25", fc="#e8f1fb" if hoja else "#fff3d6", ec="#555", lw=0.8))
    ax.set_axis_off()
    ax.margins(0.08)
    if titulo:
        ax.set_title(titulo, fontsize=11)
    fig.savefig(ruta_png, dpi=150, bbox_inches="tight")
    plt.close(fig)


def a_dot(arbol: Node) -> str:
    lineas, ids = ["digraph T {", '  node [shape=box, style=rounded, fontname="Helvetica"];'], {}
    for i, n in enumerate(_nodos(arbol)):
        ids[id(n)] = f"n{i}"
        lineas.append(f'  n{i} [label="{_etiqueta(n).replace(chr(10), " ")}"];')
    lineas += [f"  {ids[id(p)]} -> {ids[id(h)]};" for p, h in _aristas(arbol)]
    return "\n".join(lineas + ["}"])


def generar(oracion: str, attach="SV", prefijo="") -> str | None:
    r = analizar(oracion, attach)
    if not r.acepta:
        print(f"RECHAZADA: {oracion!r} -> {r.tipo_error}: {r.error}")
        return None
    os.makedirs(SALIDA, exist_ok=True)
    base = prefijo + re.sub(r"\W+", "_", oracion.lower()).strip("_")[:60]
    png = os.path.join(SALIDA, base + ".png")
    dibujar(r.arbol, png, f"{oracion}   [SP -> {attach}]")
    with open(os.path.join(SALIDA, base + ".dot"), "w") as f:
        f.write(a_dot(r.arbol))
    print(r.arbol.pretty())
    print("->", png)
    return png


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("oracion", nargs="?")
    ap.add_argument("--attach", default="SV", choices=["SV", "SN"])
    ap.add_argument("--todas", action="store_true")
    a = ap.parse_args()
    if a.todas:
        with open(os.path.join(os.path.dirname(__file__), "dataset.csv"), encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                generar(row["oracion"], a.attach, prefijo=row["id"] + "_")
    elif a.oracion:
        generar(a.oracion, a.attach)
    else:
        ap.error("indique una oración o --todas")
