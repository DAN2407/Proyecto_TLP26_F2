"""Léxico del parser de la Fase 2. Todo el vocabulario del lenguaje controlado está aquí."""
from collections import defaultdict


def _tabla(filas):
    d = defaultdict(set)
    for forma, g, n in filas:
        d[forma].add((g, n))
    return dict(d)


# forma -> {(género, número)}
DET = _tabla([("el", "m", "s"), ("la", "f", "s"), ("los", "m", "p"), ("las", "f", "p"),
              ("un", "m", "s"), ("una", "f", "s"), ("unos", "m", "p"), ("unas", "f", "p")])
NOUN = _tabla([("niño", "m", "s"), ("niña", "f", "s"), ("niños", "m", "p"), ("niñas", "f", "p"),
               ("perro", "m", "s"), ("perra", "f", "s"), ("perros", "m", "p"), ("perras", "f", "p"),
               ("libro", "m", "s"), ("libros", "m", "p"), ("casa", "f", "s"), ("casas", "f", "p"),
               ("hombre", "m", "s"), ("hombres", "m", "p"), ("mujer", "f", "s"), ("mujeres", "f", "p"),
               ("telescopio", "m", "s"), ("telescopios", "m", "p")])
ADJ = _tabla([("pequeño", "m", "s"), ("pequeña", "f", "s"), ("pequeños", "m", "p"), ("pequeñas", "f", "p"),
              ("rojo", "m", "s"), ("roja", "f", "s"), ("rojos", "m", "p"), ("rojas", "f", "p"),
              ("feliz", "m", "s"), ("feliz", "f", "s"), ("felices", "m", "p"), ("felices", "f", "p")])

# nombres propios: forma -> (género, número)
PN = {"Ana": ("f", "s"), "Luis": ("m", "s"), "Marta": ("f", "s")}

# verbos: forma -> [(número, tiempo, transitividad)]   I = intransitivo, T = transitivo
VERB = {
    "duerme": [("s", "pres", "I")], "duermen": [("p", "pres", "I")],
    "corre": [("s", "pres", "I")], "corren": [("p", "pres", "I")],
    "durmió": [("s", "pret", "I")], "durmieron": [("p", "pret", "I")],
    "corrió": [("s", "pret", "I")], "corrieron": [("p", "pret", "I")],
    "lee": [("s", "pres", "T")], "leen": [("p", "pres", "T")],
    "ve": [("s", "pres", "T")], "ven": [("p", "pres", "T")],
    "leyó": [("s", "pret", "T")], "leyeron": [("p", "pret", "T")],
    "vio": [("s", "pret", "T")], "vieron": [("p", "pret", "T")],
    "come": [("s", "pres", "I"), ("s", "pres", "T")], "comen": [("p", "pres", "I"), ("p", "pres", "T")],
    "comió": [("s", "pret", "I"), ("s", "pret", "T")], "comieron": [("p", "pret", "I"), ("p", "pret", "T")],
    # verbos que admiten completiva ("dice que...") pero la gramática NO la cubre: miden el límite.
    "dice": [("s", "pres", "T")], "dicen": [("p", "pres", "T")],
    "quiere": [("s", "pres", "T")], "quieren": [("p", "pres", "T")],
}
ADV = {"rápidamente", "ayer", "mucho"}
PREP = {"con", "en", "de"}
QUE = "que"
A_PERSONAL = "a"
HUMANOS = {"niño", "niña", "niños", "niñas", "hombre", "hombres", "mujer", "mujeres"}

VOCAB = (set(DET) | set(NOUN) | set(ADJ) | set(PN) | set(VERB) | ADV | PREP | {QUE, A_PERSONAL})
