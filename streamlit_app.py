"""Interfaz web de la Calculadora Financiera; el motor permanece en calculos.py."""
import csv
import io
import math
from datetime import datetime

import streamlit as st

from calculos import (
    EJERCICIOS, MODULOS, OPERACIONES, OP_POR_CLAVE, REGLAS,
    ErrorCalculo, ejecutar, formatear,
)

st.set_page_config(
    page_title="Calculadora Financiera | Ingeniería Económica",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Calculadora Financiera")
st.caption("Ingeniería Económica · Grupo D2")
st.write(
    "Calculadora para ejercicios de ingeniería económica. "
    "Selecciona un módulo y una operación, introduce los datos y calcula."
)

# Navegación derivada del registro original: no se duplican ni reescriben fórmulas.
modulo_ids = [m[0] for m in MODULOS]
modulo_labels = {m[0]: m[1] for m in MODULOS}
modulo_descripciones = {m[0]: m[2] for m in MODULOS}

with st.sidebar:
    st.header("Navegación")
    modulo_id = st.selectbox(
        "Módulo",
        options=modulo_ids,
        format_func=lambda value: modulo_labels[value],
    )
    st.caption(modulo_descripciones[modulo_id])
    st.divider()
    st.subheader("Convenciones")
    st.markdown(REGLAS.replace("• ", "- "))
    st.caption("La periodicidad se conserva como etiqueta y no convierte unidades automáticamente.")

operaciones_modulo = [op for op in OPERACIONES if op.modulo == modulo_id]
op = st.selectbox(
    "Operación",
    options=operaciones_modulo,
    format_func=lambda item: item.titulo,
)
st.subheader(op.titulo)
st.markdown(f"**Ecuación / método:** `{op.ecuacion}`")

if "historial_calculos" not in st.session_state:
    st.session_state.historial_calculos = []
if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None
if "ultimo_error" not in st.session_state:
    st.session_state.ultimo_error = None

def math_isclose(a, b):
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9)


def widget_key(operation_key, field_key):
    return f"campo_{operation_key}_{field_key}"


def clear_current_inputs(operation_key, field_keys):
    for field_key in field_keys:
        st.session_state.pop(widget_key(operation_key, field_key), None)
    st.session_state.ultimo_resultado = None
    st.session_state.ultimo_error = None

with st.form(key=f"form_{op.clave}"):
    st.markdown("#### Datos de entrada")
    cols = st.columns(2)
    valores = {}
    for idx, campo in enumerate(op.campos):
        with cols[idx % 2]:
            key = widget_key(op.clave, campo.clave)
            if campo.tipo == "num":
                valores[campo.clave] = st.text_input(
                    campo.etiqueta,
                    key=key,
                    placeholder=f"Introduce el valor ({campo.unidad})" if campo.unidad else "Introduce el valor",
                    help=f"Unidad: {campo.unidad}" if campo.unidad else None,
                )
            else:
                opciones = list(campo.valores)
                valores[campo.clave] = st.selectbox(
                    campo.etiqueta,
                    options=opciones,
                    key=key,
                )
    calcular = st.form_submit_button("Calcular", type="primary", use_container_width=True)

if calcular:
    try:
        resultado = ejecutar(op, valores)
        resultado_texto = formatear(resultado, op.res_unidad)
        st.session_state.ultimo_resultado = {
            "operacion": op.titulo,
            "ecuacion": op.ecuacion,
            "etiqueta": op.res_etiqueta,
            "valor": resultado,
            "formateado": resultado_texto,
            "unidad": op.res_unidad,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "entradas": {campo.etiqueta: str(valores.get(campo.clave, "")) for campo in op.campos},
        }
        st.session_state.ultimo_error = None
        st.session_state.historial_calculos.append(st.session_state.ultimo_resultado.copy())
    except ErrorCalculo as exc:
        st.session_state.ultimo_error = str(exc)
        st.session_state.ultimo_resultado = None
    except Exception as exc:
        # No ocultar errores inesperados de programación.
        st.session_state.ultimo_error = (
            "Ocurrió un error inesperado al calcular. "
            f"Detalle técnico: {type(exc).__name__}: {exc}"
        )
        st.session_state.ultimo_resultado = None

col_reset, col_space = st.columns([1, 3])
with col_reset:
    st.button(
        "Limpiar campos",
        use_container_width=True,
        on_click=clear_current_inputs,
        args=(op.clave, [campo.clave for campo in op.campos]),
    )

if st.session_state.ultimo_error:
    st.error(st.session_state.ultimo_error)

if st.session_state.ultimo_resultado:
    resultado = st.session_state.ultimo_resultado
    st.success("Cálculo realizado")
    st.metric(resultado["etiqueta"], resultado["formateado"])
    with st.expander("Ver detalle del último cálculo"):
        st.write(f"**Operación:** {resultado['operacion']}")
        st.write(f"**Ecuación / método:** {resultado['ecuacion']}")
        st.write("**Entradas utilizadas:**")
        for etiqueta, valor in resultado["entradas"].items():
            st.write(f"- {etiqueta}: {valor}")
        st.caption(f"Calculado: {resultado['fecha']}")

with st.expander("Ejercicios de referencia incluidos"):
    st.write(
        "Estos casos sirven como comprobación de regresión del motor de cálculo. "
        "No sustituyen una revisión académica independiente de las fórmulas."
    )
    filas = []
    for clave, entradas, esperado in EJERCICIOS:
        operacion = OP_POR_CLAVE[clave]
        try:
            obtenido = ejecutar(operacion, entradas)
            coincide = math_isclose(obtenido, esperado)
            filas.append({
                "Operación": operacion.titulo,
                "Resultado esperado": formatear(esperado, operacion.res_unidad),
                "Resultado calculado": formatear(obtenido, operacion.res_unidad),
                "Coincide": "Sí" if coincide else "No",
            })
        except Exception as exc:
            filas.append({
                "Operación": operacion.titulo,
                "Resultado esperado": formatear(esperado, operacion.res_unidad),
                "Resultado calculado": f"Error: {exc}",
                "Coincide": "No",
            })
    st.dataframe(filas, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Historial de esta sesión")
historial = st.session_state.historial_calculos
if not historial:
    st.info("Todavía no hay cálculos en esta sesión.")
else:
    st.dataframe(
        [
            {
                "Fecha": item["fecha"],
                "Operación": item["operacion"],
                "Resultado": item["formateado"],
                "Entradas": "; ".join(f"{k}: {v}" for k, v in item["entradas"].items()),
            }
            for item in reversed(historial)
        ],
        use_container_width=True,
        hide_index=True,
    )
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=["Fecha", "Operación", "Ecuación", "Entradas", "Resultado", "Unidad"],
    )
    writer.writeheader()
    for item in historial:
        writer.writerow({
            "Fecha": item["fecha"],
            "Operación": item["operacion"],
            "Ecuación": item["ecuacion"],
            "Entradas": "; ".join(f"{k}: {v}" for k, v in item["entradas"].items()),
            "Resultado": item["valor"],
            "Unidad": item["unidad"],
        })
    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "Descargar historial CSV",
            data="\ufeff" + csv_buffer.getvalue(),
            file_name="historial_calculadora_financiera.csv",
            mime="text/csv",
            use_container_width=True,
        )
    txt = "\n\n".join(
        f"Fecha: {item['fecha']}\nOperación: {item['operacion']}\n"
        f"Ecuación: {item['ecuacion']}\n"
        + "\n".join(f"{k}: {v}" for k, v in item["entradas"].items())
        + f"\nResultado: {item['formateado']}"
        for item in historial
    )
    with d2:
        st.download_button(
            "Descargar historial TXT",
            data=txt,
            file_name="historial_calculadora_financiera.txt",
            mime="text/plain",
            use_container_width=True,
        )

st.caption("La interfaz web usa el motor de cálculo original `calculos.py`.")
