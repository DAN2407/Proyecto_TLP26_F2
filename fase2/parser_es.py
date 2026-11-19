"""
Parser descendente recursivo para un subconjunto controlado del español (Fase 2).

GRAMÁTICA (EBNF; sin recursión por la izquierda; la concordancia se verifica
pasando rasgos (género, número) entre métodos, en vez de duplicar reglas):

  S    -> SN SV                          el verbo concuerda en número con el sujeto
  SN   -> Det N Adj* Rel?  |  PN         Det, N y Adj concuerdan en género y número
  Rel  -> 'que' SV                       el verbo de la relativa concuerda con el antecedente
  SV   -> V Obj? ( Adv | SP )*           V: presente o pretérito; I/T decide si lleva objeto
  Obj  -> 'a'? SN                        'a' solo ante nombre propio o sustantivo humano
  SP   -> Prep SN

AMBIGÜEDAD PP: "ve la mujer con el telescopio" admite 2 lecturas. Un descenso
recursivo produce UNA; el parámetro `attach` decide la política:
  attach="SV" (por defecto): el SP cuelga del verbo
  attach="SN"              : el SP cuelga del objeto

NO cubierto a propósito (nivel 3): orden VS, sujeto nulo, coordinación,
completivas ("dice que..."), subjuntivo, negación, pasivas.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from formal.tree import Node
from . import lexico as L


class ErrorAnalisis(Exception):
    def __init__(self, msg: str, pos: int, tipo: str = "sintaxis"):
        super().__init__(msg)
        self.msg, self.pos, self.tipo = msg, pos, tipo


@dataclass
class Resultado:
    oracion: str
    acepta: bool
    arbol: Optional[Node] = None
    error: str = ""
    tipo_error: str = ""            # 'sintaxis' | 'concordancia' | 'vocabulario' | ''
    pos: List[Tuple[str, str]] = field(default_factory=list)   # [(palabra, UPOS)]


def tokenizar(oracion: str) -> List[str]:
    limpio = re.sub(r"[.,;:¿?¡!]", " ", oracion)
    return [t if t in L.PN else t.lower() for t in limpio.split()]


class _Parser:
    def __init__(self, toks: List[str], attach: str):
        self.toks, self.i, self.attach = toks, 0, attach

    def act(self) -> Optional[str]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def avanzar(self) -> str:
        t = self.toks[self.i]
        self.i += 1
        return t

    def error(self, msg: str, tipo: str = "sintaxis"):
        raise ErrorAnalisis(msg, self.i, tipo)

    def _encontrado(self) -> str:
        return repr(self.act()) if self.act() is not None else "el fin de la oración"

    # --- reglas ---
    def S(self) -> Node:
        sn, n, _ = self.SN()
        sv = self.SV(n)
        return Node("S", [sn, sv])

    def SN(self):
        """Devuelve (nodo, número, palabra_núcleo)."""
        w = self.act()
        if w in L.PN:
            self.avanzar()
            _, n = L.PN[w]
            return Node("SN_pn", [Node("PN", valor=w)]), n, w
        if w not in L.DET:
            self.error(f"se esperaba un determinante o nombre propio y se encontró {self._encontrado()}")
        det = self.avanzar()
        comunes = set(L.DET[det])
        w2 = self.act()
        if w2 not in L.NOUN:
            self.error(f"se esperaba un sustantivo después de {det!r} y se encontró {self._encontrado()}")
        noun = self.avanzar()
        comunes &= L.NOUN[noun]
        if not comunes:
            self.error(f"concordancia determinante-sustantivo: {det!r} {noun!r}", "concordancia")
        adjs = []
        while self.act() in L.ADJ:
            a = self.avanzar()
            comunes &= L.ADJ[a]
            if not comunes:
                self.error(f"concordancia sustantivo-adjetivo: {noun!r} {a!r}", "concordancia")
            adjs.append(a)
        g, n = sorted(comunes)[0]
        f = f"{g}{n}"
        hijos = [Node(f"Det_{f}", valor=det), Node(f"N_{f}", valor=noun)]
        hijos += [Node(f"Adj_{f}", valor=a) for a in adjs]
        if self.act() == L.QUE:
            q = self.avanzar()
            hijos.append(Node("Rel", [Node("Que", valor=q), self.SV(n)]))
        return Node(f"SN_{f}", hijos), n, noun

    def SV(self, n: str) -> Node:
        w = self.act()
        if w not in L.VERB:
            self.error(f"se esperaba un verbo y se encontró {self._encontrado()}")
        self.avanzar()
        cand = [e for e in L.VERB[w] if e[0] == n]
        if not cand:
            self.error(f"concordancia sujeto-verbo: {w!r} no concuerda en número con el sujeto", "concordancia")
        tiempo = cand[0][1]
        trans = {e[2] for e in cand}
        hijos = [Node(f"V_{n}_{tiempo}", valor=w)]
        if self.empieza_objeto():
            if trans == {"I"}:
                self.error(f"{w!r} es intransitivo y no admite objeto")
            hijos.append(self.objeto())
        elif trans == {"T"}:
            self.error(f"{w!r} es transitivo y requiere objeto, pero se encontró {self._encontrado()}")
        while True:
            w2 = self.act()
            if w2 in L.ADV:
                hijos.append(Node("Adv", valor=self.avanzar()))
            elif w2 in L.PREP:
                hijos.append(self.SP())
            else:
                break
        return Node(f"SV_{n}", hijos)

    def empieza_objeto(self) -> bool:
        w = self.act()
        return w in L.DET or w in L.PN or w == L.A_PERSONAL

    def objeto(self) -> Node:
        personal = self.act() == L.A_PERSONAL
        a = Node("A_pers", valor=self.avanzar()) if personal else None
        sn, _, nucleo = self.SN()
        if personal and not (nucleo in L.PN or nucleo in L.HUMANOS):
            self.error("la 'a' personal solo va ante nombre propio o sustantivo humano")
        if self.attach == "SN":
            while self.act() in L.PREP:
                sn = Node(sn.tipo, [sn, self.SP()])
        return Node("Obj", [a, sn]) if personal else sn

    def SP(self) -> Node:
        prep = self.avanzar()
        sn, _, _ = self.SN()
        return Node("SP", [Node("Prep", valor=prep), sn])


_UPOS = {"Det": "DET", "N": "NOUN", "Adj": "ADJ", "V": "VERB", "Adv": "ADV",
         "Prep": "ADP", "A_pers": "ADP", "PN": "PROPN", "Que": "SCONJ"}


def etiquetas(arbol: Node) -> List[Tuple[str, str]]:
    """[(palabra, UPOS)] en orden de aparición (hojas del árbol)."""
    if arbol is None:
        return []
    if not arbol.hijos:
        clave = "A_pers" if arbol.tipo == "A_pers" else arbol.tipo.split("_")[0]
        return [(arbol.valor, _UPOS[clave])]
    out = []
    for h in arbol.hijos:
        out += etiquetas(h)
    return out


def analizar(oracion: str, attach: str = "SV") -> Resultado:
    toks = tokenizar(oracion)
    if not toks:
        return Resultado(oracion, False, error="oración vacía", tipo_error="sintaxis")
    p = _Parser(toks, attach)
    try:
        arbol = p.S()
        if p.i < len(toks):
            p.error(f"sobran palabras a partir de {toks[p.i]!r}")
    except ErrorAnalisis as e:
        tipo = e.tipo
        if tipo == "sintaxis" and e.pos < len(toks) and toks[e.pos] not in L.VOCAB:
            tipo = "vocabulario"
        return Resultado(oracion, False, error=f"posición {e.pos + 1}: {e.msg}", tipo_error=tipo)
    return Resultado(oracion, True, arbol=arbol, pos=etiquetas(arbol))


# Texto de la gramática para el prompt del LLM.
GRAMATICA_TEXTO = """\
S   -> SN SV
SN  -> Det N Adj* Rel?   |   PN
Rel -> 'que' SV
SV  -> V Obj? ( Adv | SP )*
Obj -> 'a'? SN
SP  -> Prep SN

Restricciones:
1. Det, N y todos los Adj de un SN concuerdan en género y número.
2. El verbo de S concuerda en número con el SN sujeto (un PN es singular).
3. El verbo de Rel concuerda en número con el SN que lo contiene (su antecedente).
4. Un verbo marcado I (intransitivo) no admite Obj; uno marcado T (transitivo) lo exige; I/T lo admite opcionalmente.
5. 'a' en Obj solo se permite si el SN es un PN o su sustantivo es humano (niño/a/s, hombre/s, mujer/es).
6. Adj va siempre después del N. No existen otras reglas: cualquier oración que no se derive de estas reglas debe rechazarse."""


def lexico_texto() -> str:
    def f(d):
        return ", ".join(f"{w}({'/'.join(sorted(g + n for g, n in fs))})" for w, fs in sorted(d.items()))
    verbs = ", ".join(f"{w}({e[0][0]},{e[0][1]},{'/'.join(sorted({x[2] for x in e}))})"
                      for w, e in sorted(L.VERB.items()))
    return (f"Det: {f(L.DET)}\nN: {f(L.NOUN)}\nAdj: {f(L.ADJ)}\n"
            f"PN: {', '.join(sorted(L.PN))}\nV (número,tiempo,transitividad): {verbs}\n"
            f"Adv: {', '.join(sorted(L.ADV))}\nPrep: {', '.join(sorted(L.PREP))}")
