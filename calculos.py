"""Motor de cálculo: Calculadora financiera | Ingeniería económica.

Convenciones (igual que el libro de Excel):
- Las tasas se escriben como porcentaje: 5 representa 5 %, no 0,05.
- La periodicidad es solo una etiqueta; no se convierten unidades automáticamente.
- n y m deben ser compatibles con la periodicidad de la tasa.
"""
import math
from dataclasses import dataclass


class ErrorCalculo(Exception):
    """Error de datos de entrada que se muestra al usuario."""


PERIODICIDADES = ("anual", "semestral", "cuatrimestral", "trimestral",
                  "bimestral", "mensual", "quincenal", "semanal", "diaria")


@dataclass
class Campo:
    clave: str
    etiqueta: str
    unidad: str = ""
    tipo: str = "num"      # num | lista (editable) | lista_fija
    valores: tuple = ()


@dataclass
class Operacion:
    clave: str
    modulo: str
    titulo: str
    ecuacion: str
    campos: list
    func: object
    res_etiqueta: str
    res_unidad: str
    pendiente: bool = False


# ---------------------------------------------------------------- utilidades
def _num(valor, nombre):
    if isinstance(valor, (int, float)):
        x = float(valor)
    else:
        s = str(valor).strip().replace(" ", "").replace(",", ".")
        if s == "":
            raise ErrorCalculo(f"Falta el valor de «{nombre}».")
        try:
            x = float(s)
        except ValueError:
            raise ErrorCalculo(f"«{nombre}» no es un número válido.")
    if not math.isfinite(x):
        raise ErrorCalculo(f"«{nombre}» no es un número válido.")
    return x


def _tasa(v, clave="i"):
    r = v[clave] / 100.0
    if r == 0:
        raise ErrorCalculo("La tasa no puede ser 0 en esta operación.")
    if r <= -1:
        raise ErrorCalculo("La tasa debe ser mayor que -100 %.")
    return r


def _m(v):
    if v["m"] <= 0:
        raise ErrorCalculo("Los periodos por año m deben ser mayores que 0.")
    return v["m"]


def formatear(valor, unidad=""):
    """Formato con separador de miles '.' y decimal ','."""
    unidad = unidad.strip()
    if unidad.startswith("$"):
        s = f"{valor:,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
        sufijo = unidad[1:].strip()
        return "$ " + s + (" " + sufijo if sufijo else "")
    s = f"{valor:.6f}".rstrip("0").rstrip(".").replace(".", ",")
    return s + (" " + unidad if unidad else "")


def ejecutar(op, valores):
    """Convierte las entradas, valida y calcula. Devuelve un float."""
    v = {}
    for c in op.campos:
        if c.tipo == "num":
            v[c.clave] = _num(valores.get(c.clave, ""), c.etiqueta)
        else:
            v[c.clave] = str(valores.get(c.clave, "")).strip()
    try:
        r = op.func(v)
    except ErrorCalculo:
        raise
    except (ZeroDivisionError, ValueError, OverflowError):
        raise ErrorCalculo("No se pudo calcular con esos valores "
                           "(división por cero o valores fuera de dominio).")
    if isinstance(r, complex) or not math.isfinite(r):
        raise ErrorCalculo("El resultado no es un número real con esos valores.")
    return r


# ----------------------------------------------------------- campos comunes
def N(clave, etiqueta, unidad):
    return Campo(clave, etiqueta, unidad, "num")


PER = Campo("per", "Periodicidad", "etiqueta", "lista", PERIODICIDADES)
M = N("m", "Periodos por año m", "periodos/año")


def per(etiqueta):
    return Campo("per", etiqueta, "etiqueta", "lista", PERIODICIDADES)


# ------------------------------------------------------------- 01 interés
def _ic_i(v):
    if v["P"] == 0:
        raise ErrorCalculo("El valor presente P no puede ser 0.")
    return ((v["F"] / v["P"]) ** (1 / v["n"]) - 1) * 100


def _ic_n(v):
    if v["P"] == 0:
        raise ErrorCalculo("El valor presente P no puede ser 0.")
    return math.log(v["F"] / v["P"]) / math.log(1 + v["i"] / 100)


# ------------------------------------------------------------ 03 indexadas
def _validar_indexadas(v):
    if not v["perA"] or not v["perB"]:
        raise ErrorCalculo("Indica la periodicidad de ambas tasas.")
    if not v["tipoA"] or not v["tipoB"]:
        raise ErrorCalculo("Indica el tipo (vencida/anticipada) de ambas tasas.")
    if v["perA"] != v["perB"]:
        raise ErrorCalculo("Las dos tasas deben tener la misma periodicidad.")
    if v["tipoA"] != v["tipoB"]:
        raise ErrorCalculo("Las dos tasas deben ser del mismo tipo.")


def _idx_suma(v):
    _validar_indexadas(v)
    return v["A"] + v["B"]


def _idx_comp(v):
    _validar_indexadas(v)
    return ((1 + v["A"] / 100) * (1 + v["B"] / 100) - 1) * 100


def _campos_idx_ok(indicadores):
    tipos = ("vencida", "anticipada")
    return [
        Campo("ind", "Indicador (etiqueta)", "indicador", "lista", indicadores),
        N("A", "Tasa A", "%"),
        Campo("perA", "Periodicidad tasa A", "etiqueta", "lista", PERIODICIDADES),
        Campo("tipoA", "Tipo de tasa A", "tipo", "lista_fija", tipos),
        N("B", "Tasa B", "%"),
        Campo("perB", "Periodicidad tasa B", "etiqueta", "lista", PERIODICIDADES),
        Campo("tipoB", "Tipo de tasa B", "tipo", "lista_fija", tipos),
    ]


# --------------------------------------------------------- anualidades
def _fa(i, n):
    return ((1 + i) ** (n - 1) - 1) / (i * (1 + i) ** (n - 1))


def _venc_P(v):
    i = _tasa(v)
    return v["A"] * ((1 + i) ** v["n"] - 1) / (i * (1 + i) ** v["n"])


def _venc_A_P(v):
    i = _tasa(v)
    return v["P"] * (i * (1 + i) ** v["n"]) / ((1 + i) ** v["n"] - 1)


def _venc_F(v):
    i = _tasa(v)
    return v["A"] * ((1 + i) ** v["n"] - 1) / i


def _venc_A_F(v):
    i = _tasa(v)
    return v["F"] * i / ((1 + i) ** v["n"] - 1)


def _venc_n(v):
    i = _tasa(v)
    return math.log(v["F"] * i / v["A"] + 1) / math.log(1 + i)


def _ant_P(v):
    i = _tasa(v)
    return v["A"] + v["A"] * _fa(i, v["n"])


def _ant_A_P(v):
    i = _tasa(v)
    return v["P"] / (1 + _fa(i, v["n"]))


def _ant_F(v):
    i = _tasa(v)
    return v["A"] * (((1 + i) ** (v["n"] + 1) - (1 + i)) / i)


def _ant_A_F(v):
    i = _tasa(v)
    return v["F"] * i / ((1 + i) ** (v["n"] + 1) - (1 + i))


def _ant_n(v):
    """n despejado de P = A·[1 + ((1+i)^(n−1) − 1) / (i·(1+i)^(n−1))]."""
    i = _tasa(v)
    if v["A"] <= 0 or v["P"] <= 0:
        raise ErrorCalculo("La cuota A y el valor presente P deben ser mayores que 0.")
    x = 1 - i * (v["P"] / v["A"] - 1)
    if x <= 0:
        raise ErrorCalculo("Con esa tasa, el valor presente es demasiado grande para la cuota: "
                           "no se alcanza con ningún número de periodos.")
    return 1 - math.log(x) / math.log(1 + i)


def _ant_i(v):
    """Tasa i por bisección sobre la misma ecuación del valor presente."""
    A, P, n = v["A"], v["P"], v["n"]
    if A <= 0 or P <= 0:
        raise ErrorCalculo("La cuota A y el valor presente P deben ser mayores que 0.")
    if n <= 1:
        raise ErrorCalculo("El número de periodos n debe ser mayor que 1.")

    def f(i):
        if abs(i) < 1e-12:
            return A * n - P
        return A * (1 + _fa(i, n)) - P

    if P > A * n:
        raise ErrorCalculo("El valor presente P no puede ser mayor que la cuota por el número "
                           "de periodos (A·n) para una tasa positiva.")
    lo, hi = 0.0, 1000.0             # f es decreciente en i
    if f(hi) > 0:
        raise ErrorCalculo("No existe una tasa que cumpla esos datos.")
    for _ in range(300):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2 * 100


def _per_P(v):
    return v["A"] / _tasa(v)


def _per_A(v):
    return v["P"] * _tasa(v)


def _per_i(v):
    return v["A"] / v["P"] * 100


# -------------------------------------------------------------- registro
OPERACIONES = [
    # 01 INTERÉS COMPUESTO
    Operacion("ic_F", "interes", "Valor futuro F",
              "F = P · (1 + i)^n  |  La tasa y n deben referirse al mismo periodo.",
              [N("P", "Valor presente P", "$"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER],
              lambda v: v["P"] * (1 + v["i"] / 100) ** v["n"], "Valor futuro F", "$"),
    Operacion("ic_P", "interes", "Valor presente P", "P = F / (1 + i)^n",
              [N("F", "Valor futuro F", "$"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER],
              lambda v: v["F"] / (1 + v["i"] / 100) ** v["n"], "Valor presente P", "$"),
    Operacion("ic_i", "interes", "Tasa de interés i", "i = [(F/P)^(1/n) − 1] · 100",
              [N("F", "Valor futuro F", "$"), N("P", "Valor presente P", "$"),
               N("n", "Número de periodos n", "periodos"), PER],
              _ic_i, "Tasa i", "% por periodo"),
    Operacion("ic_n", "interes", "Tiempo n", "n = LN(F/P) / LN(1 + i)",
              [N("F", "Valor futuro F", "$"), N("P", "Valor presente P", "$"),
               N("i", "Tasa de interés i", "% por periodo"), PER],
              _ic_n, "Número de periodos n", "periodos"),

    # 02 CONVERSIÓN DE TASAS
    Operacion("t_nom_per", "tasas", "Nominal → Periódica", "iₚ = iₙ / m",
              [N("in", "Tasa nominal anual iₙ", "%"), M, per("Periodicidad (etiqueta)")],
              lambda v: v["in"] / _m(v), "Tasa periódica iₚ", "% por periodo"),
    Operacion("t_per_nom", "tasas", "Periódica → Nominal", "iₙ = iₚ · m",
              [N("ip", "Tasa periódica iₚ", "%"), M, per("Periodicidad (etiqueta)")],
              lambda v: v["ip"] * _m(v), "Tasa nominal iₙ", "% nominal anual"),
    Operacion("t_nom_ea", "tasas", "Nominal → Efectiva anual", "iₑₐ = [(1 + iₙ/m)^m − 1] · 100",
              [N("in", "Tasa nominal anual iₙ", "%"), M, per("Capitalización (etiqueta)")],
              lambda v: ((1 + v["in"] / 100 / _m(v)) ** v["m"] - 1) * 100,
              "Tasa efectiva iₑₐ", "% efectiva anual"),
    Operacion("t_ea_nom", "tasas", "Efectiva anual → Nominal", "iₙ = [(1 + iₑₐ)^(1/m) − 1] · m · 100",
              [N("ea", "Tasa efectiva anual iₑₐ", "%"), M, per("Capitalización deseada")],
              lambda v: ((1 + v["ea"] / 100) ** (1 / _m(v)) - 1) * v["m"] * 100,
              "Tasa nominal iₙ", "% nominal anual"),
    Operacion("t_per_ea", "tasas", "Periódica → Efectiva anual", "iₑₐ = [(1 + iₚ)^m − 1] · 100",
              [N("ip", "Tasa periódica iₚ", "%"), M, per("Periodicidad de iₚ")],
              lambda v: ((1 + v["ip"] / 100) ** _m(v) - 1) * 100,
              "Tasa efectiva iₑₐ", "% efectiva anual"),
    Operacion("t_ea_per", "tasas", "Efectiva anual → Periódica", "iₚ = [(1 + iₑₐ)^(1/m) − 1] · 100",
              [N("ea", "Tasa efectiva anual iₑₐ", "%"), M, per("Periodicidad deseada")],
              lambda v: ((1 + v["ea"] / 100) ** (1 / _m(v)) - 1) * 100,
              "Tasa periódica iₚ", "% por periodo"),
    Operacion("t_venc_ant", "tasas", "Vencida → Anticipada", "iₐ = iᵥ / (1 + iᵥ)",
              [N("iv", "Tasa vencida iᵥ", "%"), per("Periodicidad")],
              lambda v: (v["iv"] / 100) / (1 + v["iv"] / 100) * 100,
              "Tasa anticipada iₐ", "% anticipada"),
    Operacion("t_ant_venc", "tasas", "Anticipada → Vencida", "iᵥ = iₐ / (1 − iₐ)",
              [N("ia", "Tasa anticipada iₐ", "%"), per("Periodicidad")],
              lambda v: (v["ia"] / 100) / (1 - v["ia"] / 100) * 100,
              "Tasa vencida iᵥ", "% vencida"),

    # 03 TASAS INDEXADAS
    Operacion("idx_suma", "indexadas", "DTF / IBR | Suma lineal", "i = A + B",
              _campos_idx_ok(("DTF", "IBR")), _idx_suma, "Resultado i", "% combinación lineal"),
    Operacion("idx_comp", "indexadas", "IPC / UVR | Combinación compuesta",
              "i = [(1 + A)(1 + B) − 1] · 100",
              _campos_idx_ok(("IPC", "UVR")), _idx_comp, "Resultado i", "% combinación compuesta"),

    # 04 ANUALIDAD VENCIDA
    Operacion("v_P", "vencida", "Valor presente (a partir de la cuota)",
              "P = A · [((1+i)^n − 1) / (i · (1+i)^n)]",
              [N("A", "Cuota A", "$ por periodo"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _venc_P, "Valor presente P", "$"),
    Operacion("v_A_P", "vencida", "Cuota (a partir del valor presente)",
              "A = P · [i(1+i)^n / ((1+i)^n − 1)]",
              [N("P", "Valor presente P", "$"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _venc_A_P, "Cuota A", "$ por periodo"),
    Operacion("v_F", "vencida", "Valor futuro (a partir de la cuota)",
              "F = A · [((1+i)^n − 1) / i]",
              [N("A", "Cuota A", "$ por periodo"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _venc_F, "Valor futuro F", "$"),
    Operacion("v_A_F", "vencida", "Cuota (a partir del valor futuro)",
              "A = F · [i / ((1+i)^n − 1)]",
              [N("F", "Valor futuro F", "$"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _venc_A_F, "Cuota A", "$ por periodo"),
    Operacion("v_n", "vencida", "Número de periodos",
              "n = LN(F·i/A + 1) / LN(1 + i)",
              [N("F", "Valor futuro F", "$"), N("A", "Cuota A", "$ por periodo"),
               N("i", "Tasa de interés i", "% por periodo"), PER], _venc_n, "Número de periodos n", "periodos"),

    # 05 ANUALIDAD ANTICIPADA
    Operacion("a_P", "anticipada", "Valor presente (a partir de la cuota)",
              "P = A + A · [((1+i)^(n−1) − 1) / (i · (1+i)^(n−1))]",
              [N("A", "Cuota A", "$ por periodo"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _ant_P, "Valor presente P", "$"),
    Operacion("a_A_P", "anticipada", "Cuota (a partir del valor presente)",
              "A = P / {1 + [((1+i)^(n−1) − 1) / (i · (1+i)^(n−1))]}",
              [N("P", "Valor presente P", "$"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _ant_A_P, "Cuota A", "$ por periodo"),
    Operacion("a_F", "anticipada", "Valor futuro (a partir de la cuota)",
              "F = A · [((1+i)^(n+1) − (1+i)) / i]",
              [N("A", "Cuota A", "$ por periodo"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _ant_F, "Valor futuro F", "$"),
    Operacion("a_A_F", "anticipada", "Cuota (a partir del valor futuro)",
              "A = F · i / ((1+i)^(n+1) − (1+i))",
              [N("F", "Valor futuro F", "$"), N("i", "Tasa de interés i", "% por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _ant_A_F, "Cuota A", "$ por periodo"),
    Operacion("a_i", "anticipada", "Tasa de interés",
              "Se obtiene por aproximación numérica a partir de P, A y n.",
              [N("P", "Valor presente P", "$"), N("A", "Cuota A", "$ por periodo"),
               N("n", "Número de periodos n", "periodos"), PER], _ant_i, "Tasa i", "% por periodo"),
    Operacion("a_n", "anticipada", "Número de periodos",
              "Se despeja n de la ecuación del valor presente.",
              [N("P", "Valor presente P", "$"), N("A", "Cuota A", "$ por periodo"),
               N("i", "Tasa de interés i", "% por periodo"), PER], _ant_n,
              "Número de periodos n", "periodos"),

    # 06 ANUALIDAD PERPETUA
    Operacion("p_P", "perpetua", "Capital requerido", "P = A / i",
              [N("A", "Pago periódico A", "$ por periodo"), N("i", "Tasa de interés i", "% por periodo"), PER],
              _per_P, "Capital requerido P", "$"),
    Operacion("p_A", "perpetua", "Pago periódico sostenible", "A = P · i",
              [N("P", "Capital disponible P", "$"), N("i", "Tasa de interés i", "% por periodo"), PER],
              _per_A, "Pago periódico A", "$ por periodo"),
    Operacion("p_i", "perpetua", "Tasa de interés", "i = (A / P) · 100",
              [N("A", "Pago periódico A", "$ por periodo"), N("P", "Capital P", "$"), PER],
              _per_i, "Tasa i", "% por periodo"),
]

OP_POR_CLAVE = {op.clave: op for op in OPERACIONES}

MODULOS = [
    ("interes", "01  Interés compuesto", "Calcula valor futuro, valor presente, tasa o tiempo."),
    ("tasas", "02  Conversión de tasas",
     "Convierte tasas nominales, periódicas, efectivas, vencidas y anticipadas."),
    ("indexadas", "03  Tasas indexadas", "Combina tasas DTF/IBR por suma e IPC/UVR por composición."),
    ("vencida", "04  Anualidad vencida", "Valor presente, valor futuro, cuotas y número de periodos."),
    ("anticipada", "05  Anualidad anticipada", "Valor presente, valor futuro y cuotas anticipadas."),
    ("perpetua", "06  Anualidad perpetua", "Capital requerido, pago periódico o tasa."),
]

REGLAS = (
    "• Tasas: escribe 5 para representar 5 %; no escribas 0,05.\n"
    "• Tiempo n y periodos por año m deben ser compatibles con la periodicidad de la tasa.\n"
    "• La periodicidad se usa como etiqueta; no se convierten unidades automáticamente.\n"
    "• Las tasas indexadas solo se calculan cuando ambas tasas tienen igual periodicidad y tipo.\n"
    "• Anualidad anticipada: la tasa i se calcula por aproximación numérica y n despejando el valor presente."
)

# Ejercicios de referencia tomados del libro de Excel: (operación, entradas, resultado esperado)
EJERCICIOS = [
    ("ic_F", {"P": 68000000, "i": 8, "n": 16}, 232964099.74672106),
    ("ic_P", {"F": 50000000, "i": 12, "n": 2}, 39859693.877551012),
    ("ic_i", {"F": 6500000, "P": 5800000, "n": 15}, 0.76252089159374314),
    ("ic_n", {"F": 254000000, "P": 986000, "i": 21}, 29.122981421267514),
    ("t_nom_per", {"in": 15, "m": 50}, 0.3),
    ("idx_comp", {"A": 15, "B": 10, "perA": "semestral", "perB": "semestral",
                  "tipoA": "anticipada", "tipoB": "anticipada"}, 26.499999999999989),
    ("a_A_P", {"P": 8500000, "i": 15, "n": 9}, 1549025.3283108275),
    ("a_i", {"P": 8500000, "A": 1549025.3283108275, "n": 9}, 15.0),
    ("a_n", {"P": 8500000, "A": 1549025.3283108275, "i": 15}, 9.0),
    ("p_P", {"A": 152000, "i": 12}, 1266666.6666666667),
    ("p_i", {"A": 1500000, "P": 15000225}, 9.9998500022499659),
]
