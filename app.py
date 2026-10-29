"""Calculadora financiera | Ingeniería económica (aplicación de escritorio)."""
import csv
import datetime
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from calculos import (EJERCICIOS, MODULOS, OP_POR_CLAVE, OPERACIONES, REGLAS,
                      ErrorCalculo, ejecutar, formatear)

# ------------------------------------------------------------------ estilo
C = {
    "lateral": "#10243b", "lateral_hover": "#183454", "lateral_activo": "#214770",
    "texto_lateral": "#b9c8dc", "texto_activo": "#ffffff", "titulo_lateral": "#ffffff",
    "seccion_lateral": "#6f87a6", "linea_lateral": "#183454", "fondo": "#f2f5fa",
    "tarjeta": "#ffffff", "borde": "#dfe5ef", "texto": "#1b2635", "suave": "#6b7a90",
    "acento": "#2563eb", "acento_osc": "#1d4ed8", "acento_claro": "#eaf1ff",
    "celeste": "#2563eb", "ecuacion": "#f4f6fb", "ok": "#15803d", "ok_fondo": "#e7f6ec",
    "mal": "#b42318", "mal_fondo": "#fdecea", "pend": "#b45309", "pend_fondo": "#fff4e0",
}
FUENTE = "TkDefaultFont"


def F(tam=10, peso="normal"):
    return (FUENTE, tam, peso)


def elegir_fuente():
    disponibles = set(tkfont.families())
    for nombre in ("Segoe UI", "Helvetica Neue", "Calibri", "DejaVu Sans", "Arial"):
        if nombre in disponibles:
            return nombre
    return "TkDefaultFont"


def clicable(widget, comando):
    """Hace clicable un widget y todos sus hijos."""
    widget.bind("<Button-1>", lambda e: comando(), add="+")
    for hijo in widget.winfo_children():
        clicable(hijo, comando)


class Boton(tk.Label):
    ESTILOS = {
        "primario": (C["acento"], C["acento_osc"], "#ffffff"),
        "secundario": ("#e8edf5", "#d9e1ee", C["texto"]),
        "claro": (C["acento_claro"], "#d6e4ff", C["acento"]),
    }

    def __init__(self, parent, texto, comando, estilo="primario"):
        bg, hover, fg = self.ESTILOS[estilo]
        super().__init__(parent, text=texto, bg=bg, fg=fg, font=F(10, "bold"),
                         padx=16, pady=7, cursor="hand2")
        self._bg, self._hover = bg, hover
        self.bind("<Enter>", lambda e: self.configure(bg=self._hover))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg))
        self.bind("<Button-1>", lambda e: comando())


class ItemMenu(tk.Frame):
    def __init__(self, parent, texto, comando):
        super().__init__(parent, bg=C["lateral"], cursor="hand2")
        self.barra = tk.Frame(self, width=4, bg=C["lateral"])
        self.barra.pack(side="left", fill="y")
        self.lbl = tk.Label(self, text=texto, anchor="w", font=F(10), padx=14, pady=9,
                            bg=C["lateral"], fg=C["texto_lateral"])
        self.lbl.pack(side="left", fill="x", expand=True)
        self.activo = False
        for w in (self, self.lbl, self.barra):
            w.bind("<Enter>", lambda e: self._pintar(True))
            w.bind("<Leave>", lambda e: self._pintar(False))
            w.bind("<Button-1>", lambda e: comando())

    def _pintar(self, hover=False):
        if self.activo:
            bg, fg, barra, fuente = C["lateral_activo"], C["texto_activo"], C["celeste"], F(10, "bold")
        else:
            bg = C["lateral_hover"] if hover else C["lateral"]
            fg, barra, fuente = C["texto_lateral"], bg, F(10)
        self.configure(bg=bg)
        self.lbl.configure(bg=bg, fg=fg, font=fuente)
        self.barra.configure(bg=barra)

    def marcar(self, activo):
        self.activo = activo
        self._pintar()


class ScrollFrame(tk.Frame):
    """Página con desplazamiento vertical."""

    def __init__(self, parent):
        super().__init__(parent, bg=C["fondo"])
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=C["fondo"])
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=C["fondo"])
        self.al_cambiar_ancho = None
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._ventana = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", self._ajustar)
        self.canvas.configure(yscrollcommand=barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def _ajustar(self, e):
        self.canvas.itemconfigure(self._ventana, width=e.width)
        if self.al_cambiar_ancho:
            self.al_cambiar_ancho(e.width)


class Tarjeta(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["tarjeta"], highlightthickness=1,
                         highlightbackground=C["borde"], highlightcolor=C["borde"], **kw)


class Bloque(Tarjeta):
    """Una operación: campos de entrada, botón Calcular y resultado."""

    def __init__(self, parent, app, op):
        super().__init__(parent)
        self.app, self.op, self.vars = app, op, {}
        cuerpo = tk.Frame(self, bg=C["tarjeta"])
        cuerpo.pack(fill="both", expand=True, padx=18, pady=16)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.columnconfigure(2, minsize=92)

        tk.Label(cuerpo, text=op.titulo, font=F(12, "bold"), fg=C["texto"], bg=C["tarjeta"],
                 anchor="w", justify="left").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        self.eq = None

        if op.pendiente:
            tk.Label(cuerpo, text="PENDIENTE", font=F(8, "bold"), fg=C["pend"], bg=C["pend_fondo"],
                     padx=8, pady=3).grid(row=1, column=0, sticky="w")
            return

        fila = 2
        for c in op.campos:
            tk.Label(cuerpo, text=c.etiqueta, font=F(9), fg=C["texto"], bg=C["tarjeta"],
                     anchor="w").grid(row=fila, column=0, sticky="w", padx=(0, 10), pady=3)
            var = tk.StringVar()
            self.vars[c.clave] = var
            if c.tipo == "num":
                w = ttk.Entry(cuerpo, textvariable=var, width=18, font=F(10))
                w.bind("<Return>", lambda e: self.calcular())
            elif c.tipo == "lista":
                w = ttk.Combobox(cuerpo, textvariable=var, values=c.valores, width=16, font=F(10))
            else:
                w = ttk.Combobox(cuerpo, textvariable=var, values=c.valores, width=16,
                                 font=F(10), state="readonly")
            w.grid(row=fila, column=1, sticky="ew", pady=3)
            tk.Label(cuerpo, text=c.unidad, font=F(8), fg=C["suave"], bg=C["tarjeta"],
                     anchor="w").grid(row=fila, column=2, sticky="w", padx=(8, 0))
            fila += 1

        botones = tk.Frame(cuerpo, bg=C["tarjeta"])
        botones.grid(row=fila, column=0, columnspan=3, sticky="w", pady=(12, 8))
        Boton(botones, "Calcular", self.calcular).pack(side="left")
        Boton(botones, "Limpiar", self.limpiar, "secundario").pack(side="left", padx=(8, 0))

        caja = tk.Frame(cuerpo, bg=C["acento_claro"])
        caja.grid(row=fila + 1, column=0, columnspan=3, sticky="ew")
        caja.columnconfigure(0, weight=1)
        tk.Label(caja, text=op.res_etiqueta.upper(), font=F(8, "bold"), fg=C["suave"],
                 bg=C["acento_claro"], anchor="w").grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))
        self.res = tk.StringVar(value="—")
        tk.Label(caja, textvariable=self.res, font=F(15, "bold"), fg=C["acento"],
                 bg=C["acento_claro"], anchor="w").grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))
        Boton(caja, "Copiar", self.copiar, "claro").grid(row=0, column=1, rowspan=2, padx=8)
        self.error = tk.Label(cuerpo, text="", font=F(9), fg=C["mal"], bg=C["tarjeta"],
                              anchor="w", justify="left", wraplength=330)
        self.error.grid(row=fila + 2, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def calcular(self):
        entradas = {k: v.get() for k, v in self.vars.items()}
        try:
            r = ejecutar(self.op, entradas)
        except ErrorCalculo as e:
            self.res.set("—")
            self.error.configure(text="⚠ " + str(e))
            return
        self.error.configure(text="")
        texto = formatear(r, self.op.res_unidad)
        self.res.set(texto)
        self.app.registrar(self.op, entradas, texto)

    def limpiar(self):
        for v in self.vars.values():
            v.set("")
        self.res.set("—")
        self.error.configure(text="")

    def copiar(self):
        if self.res.get() != "—":
            self.clipboard_clear()
            self.clipboard_append(self.res.get())

    def ajustar(self, ancho):
        if self.eq is not None:
            self.eq.configure(wraplength=ancho)
        if hasattr(self, "error"):
            self.error.configure(wraplength=ancho)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        global FUENTE
        FUENTE = elegir_fuente()
        self.title("Calculadora financiera | Ingeniería económica")
        self.geometry("1240x780")
        self.minsize(1080, 640)
        self.configure(bg=C["fondo"])
        self.historial = []
        self.var_validados = tk.StringVar(value="—")
        self.nombre_mod = {m[0]: m[1].split(None, 1)[1] for m in MODULOS}
        self._estilos()

        self.items, self.paginas, self.titulos = {}, {}, {}
        self.actual = None

        self._lateral()
        derecha = tk.Frame(self, bg=C["fondo"])
        derecha.pack(side="left", fill="both", expand=True)
        cab = tk.Frame(derecha, bg=C["fondo"])
        cab.pack(fill="x", padx=30, pady=(22, 10))
        self.lbl_titulo = tk.Label(cab, font=F(20, "bold"), fg=C["texto"], bg=C["fondo"], anchor="w")
        self.lbl_titulo.pack(fill="x")
        self.lbl_sub = tk.Label(cab, font=F(10), fg=C["suave"], bg=C["fondo"], anchor="w")
        self.lbl_sub.pack(fill="x")
        self.cuerpo = tk.Frame(derecha, bg=C["fondo"])
        self.cuerpo.pack(fill="both", expand=True, padx=(22, 8), pady=(0, 8))
        self.cuerpo.rowconfigure(0, weight=1)
        self.cuerpo.columnconfigure(0, weight=1)

        self._crear_inicio()
        for clave, nombre, desc in MODULOS:
            self._crear_modulo(clave, nombre, desc)
        self._crear_validacion()
        self._crear_reporte()

        self.bind_all("<MouseWheel>", self._rueda)
        self.bind_all("<Button-4>", lambda e: self._rueda(e, -1))
        self.bind_all("<Button-5>", lambda e: self._rueda(e, 1))
        self.validar()
        self.mostrar("inicio")

    # ---------------------------------------------------------------- estilos
    def _estilos(self):
        self.option_add("*TCombobox*Listbox.font", F(10))
        e = ttk.Style(self)
        e.theme_use("clam")
        e.configure("TEntry", padding=6, fieldbackground="#ffffff", bordercolor=C["borde"],
                    lightcolor="#ffffff", darkcolor="#ffffff")
        e.map("TEntry", bordercolor=[("focus", C["acento"])], lightcolor=[("focus", C["acento"])],
              darkcolor=[("focus", C["acento"])])
        e.configure("TCombobox", padding=5, fieldbackground="#ffffff", bordercolor=C["borde"],
                    lightcolor="#ffffff", darkcolor="#ffffff", arrowsize=14, background="#e8edf5")
        e.map("TCombobox", fieldbackground=[("readonly", "#ffffff")],
              bordercolor=[("focus", C["acento"])], lightcolor=[("focus", C["acento"])],
              darkcolor=[("focus", C["acento"])])
        e.configure("Treeview", rowheight=32, font=F(10), background="#ffffff",
                    fieldbackground="#ffffff", foreground=C["texto"], borderwidth=0)
        e.map("Treeview", background=[("selected", "#dbe7ff")], foreground=[("selected", C["texto"])])
        e.configure("Treeview.Heading", font=F(9, "bold"), background="#e9eef7",
                    foreground=C["texto"], relief="flat", padding=(8, 8))
        e.map("Treeview.Heading", background=[("active", "#dde5f2")])
        e.configure("Vertical.TScrollbar", troughcolor=C["fondo"], background="#c3cddd",
                    bordercolor=C["fondo"], arrowcolor=C["suave"], relief="flat")

    # ---------------------------------------------------------------- lateral
    def _lateral(self):
        lat = tk.Frame(self, bg=C["lateral"], width=236)
        lat.pack(side="left", fill="y")
        lat.pack_propagate(False)
        logo = tk.Frame(lat, bg=C["lateral"])
        logo.pack(fill="x", padx=20, pady=(26, 18))
        tk.Label(logo, text="Ingeniería\nEconómica", font=F(18, "bold"), fg=C["titulo_lateral"],
                 bg=C["lateral"], justify="left", anchor="w").pack(anchor="w")
        tk.Label(logo, text="Calculadora financiera", font=F(9), fg=C["texto_lateral"],
                 bg=C["lateral"]).pack(anchor="w", pady=(4, 0))
        tk.Frame(lat, bg=C["linea_lateral"], height=1).pack(fill="x", padx=20, pady=(0, 10))

        def seccion(texto):
            tk.Label(lat, text=texto, font=F(8, "bold"), fg=C["seccion_lateral"], bg=C["lateral"],
                     anchor="w").pack(fill="x", padx=20, pady=(12, 4))

        def item(clave, texto):
            it = ItemMenu(lat, texto, lambda c=clave: self.mostrar(c))
            it.pack(fill="x")
            self.items[clave] = it

        item("inicio", "Inicio")
        seccion("MÓDULOS DE CÁLCULO")
        for clave, nombre, _ in MODULOS:
            item(clave, nombre)
        seccion("HERRAMIENTAS")
        item("validacion", "07  Validación")
        item("reporte", "08  Reporte")

    # ------------------------------------------------------------- navegación
    def mostrar(self, clave):
        for k, it in self.items.items():
            it.marcar(k == clave)
        titulo, sub = self.titulos[clave]
        self.lbl_titulo.configure(text=titulo)
        self.lbl_sub.configure(text=sub)
        self.paginas[clave].tkraise()
        self.actual = clave
        if clave in self.paginas and hasattr(self.paginas[clave], "canvas"):
            self.paginas[clave].canvas.yview_moveto(0)

    def _rueda(self, e, direccion=None):
        pagina = self.paginas.get(self.actual)
        if pagina is None or not hasattr(pagina, "canvas"):
            return
        if direccion is None:
            direccion = -1 if e.delta > 0 else 1
        pagina.canvas.yview_scroll(direccion * 2, "units")

    def _registrar_pagina(self, clave, pagina, titulo, sub):
        pagina.grid(row=0, column=0, sticky="nsew")
        self.paginas[clave] = pagina
        self.titulos[clave] = (titulo, sub)

    # ----------------------------------------------------------------- inicio
    def _crear_inicio(self):
        marco = ScrollFrame(self.cuerpo)
        self._registrar_pagina("inicio", marco, "Centro de navegación",
                               "Elige un módulo para empezar a calcular.")
        f = marco.inner
        f.columnconfigure((0, 1), weight=1, uniform="col")

        # indicadores
        implementadas = sum(1 for o in OPERACIONES if not o.pendiente)
        pendientes = sum(1 for o in OPERACIONES if o.pendiente)
        kpis = tk.Frame(f, bg=C["fondo"])
        kpis.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        kpis.columnconfigure((0, 1, 2, 3), weight=1, uniform="k")
        datos = [("Ecuaciones implementadas", str(implementadas), None),
                 ("Operaciones pendientes", str(pendientes), None),
                 ("Módulos de cálculo", str(len(MODULOS)), None),
                 ("Ejercicios validados", None, self.var_validados)]
        for col, (txt, val, var) in enumerate(datos):
            t = Tarjeta(kpis)
            t.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0))
            tk.Label(t, text=txt.upper(), font=F(8, "bold"), fg=C["suave"], bg=C["tarjeta"],
                     anchor="w").pack(fill="x", padx=16, pady=(14, 0))
            lbl = tk.Label(t, font=F(24, "bold"), fg=C["acento"], bg=C["tarjeta"], anchor="w")
            if var is not None:
                lbl.configure(textvariable=var)
            else:
                lbl.configure(text=val)
            lbl.pack(fill="x", padx=16, pady=(0, 12))

        # tarjetas de navegación
        destinos = list(MODULOS) + [
            ("validacion", "07  Validación de ejercicios",
             "Compara los ejercicios del libro de Excel con el resultado calculado."),
            ("reporte", "08  Reporte", "Historial de cálculos con exportación a CSV o TXT.")]
        self._desc_nav = []
        for idx, (clave, nombre, desc) in enumerate(destinos):
            num, titulo = nombre.split(None, 1)
            t = Tarjeta(f, cursor="hand2")
            t.grid(row=1 + idx // 2, column=idx % 2, sticky="nsew",
                   padx=(0 if idx % 2 == 0 else 6, 6 if idx % 2 == 0 else 0), pady=6)
            fila = tk.Frame(t, bg=C["tarjeta"])
            fila.pack(fill="both", expand=True, padx=18, pady=16)
            tk.Label(fila, text=num, font=F(18, "bold"), fg=C["acento"], bg=C["acento_claro"],
                     width=3, pady=6).pack(side="left", anchor="n")
            texto = tk.Frame(fila, bg=C["tarjeta"])
            texto.pack(side="left", fill="x", expand=True, padx=(14, 0))
            tk.Label(texto, text=titulo, font=F(12, "bold"), fg=C["texto"], bg=C["tarjeta"],
                     anchor="w").pack(fill="x")
            d = tk.Label(texto, text=desc, font=F(9), fg=C["suave"], bg=C["tarjeta"],
                         anchor="w", justify="left", wraplength=300)
            d.pack(fill="x", pady=(2, 0))
            self._desc_nav.append(d)
            clicable(t, lambda c=clave: self.mostrar(c))
            t.bind("<Enter>", lambda e, w=t: w.configure(highlightbackground=C["acento"]))
            t.bind("<Leave>", lambda e, w=t: w.configure(highlightbackground=C["borde"]))

        # reglas
        reglas = Tarjeta(f)
        reglas.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 20))
        tk.Label(reglas, text="REGLAS IMPORTANTES", font=F(8, "bold"), fg=C["pend"],
                 bg=C["tarjeta"], anchor="w").pack(fill="x", padx=18, pady=(14, 4))
        self.lbl_reglas = tk.Label(reglas, text=REGLAS, font=F(10), fg=C["texto"], bg=C["tarjeta"],
                                   justify="left", anchor="w", wraplength=700)
        self.lbl_reglas.pack(fill="x", padx=18, pady=(0, 14))

        def ajustar(ancho):
            for d in self._desc_nav:
                d.configure(wraplength=max(ancho // 2 - 150, 120))
            self.lbl_reglas.configure(wraplength=max(ancho - 70, 200))

        marco.al_cambiar_ancho = ajustar

    # ---------------------------------------------------------------- módulos
    def _crear_modulo(self, clave, nombre, desc):
        marco = ScrollFrame(self.cuerpo)
        self._registrar_pagina(clave, marco, nombre.split(None, 1)[1], desc)
        f = marco.inner
        f.columnconfigure((0, 1), weight=1, uniform="col")
        bloques = []
        for idx, op in enumerate(o for o in OPERACIONES if o.modulo == clave):
            b = Bloque(f, self, op)
            b.grid(row=idx // 2, column=idx % 2, sticky="nsew",
                   padx=(0 if idx % 2 == 0 else 6, 6 if idx % 2 == 0 else 0), pady=6)
            bloques.append(b)
        marco.al_cambiar_ancho = lambda ancho: [b.ajustar(max(ancho // 2 - 70, 200)) for b in bloques]

    # ------------------------------------------------------------- validación
    def _crear_validacion(self):
        marco = tk.Frame(self.cuerpo, bg=C["fondo"])
        self._registrar_pagina("validacion", marco, "Validación de ejercicios",
                               "Ejercicios del libro de Excel contra el resultado calculado por la aplicación.")
        barra = tk.Frame(marco, bg=C["fondo"])
        barra.pack(fill="x", pady=(0, 10), padx=(0, 14))
        Boton(barra, "Validar de nuevo", self.validar).pack(side="right")

        caja = Tarjeta(marco)
        caja.pack(fill="both", expand=True, padx=(0, 14), pady=(0, 14))
        cols = ("modulo", "operacion", "entradas", "esperado", "calculado", "estado")
        self.tv_val = ttk.Treeview(caja, columns=cols, show="headings")
        for c, t, w in zip(cols, ("Módulo", "Operación", "Entradas", "Esperado", "Calculado", "Estado"),
                           (135, 150, 190, 170, 170, 75)):
            self.tv_val.heading(c, text=t)
            self.tv_val.column(c, width=w, minwidth=60, anchor="w")
        self.tv_val.tag_configure("ok", foreground=C["ok"])
        self.tv_val.tag_configure("mal", foreground=C["mal"])
        sb = ttk.Scrollbar(caja, orient="vertical", command=self.tv_val.yview)
        self.tv_val.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv_val.pack(side="left", fill="both", expand=True, padx=1, pady=1)

    def validar(self):
        self.tv_val.delete(*self.tv_val.get_children())
        correctos = 0
        for clave, entradas, esperado in EJERCICIOS:
            op = OP_POR_CLAVE[clave]
            try:
                r = ejecutar(op, entradas)
                calc = formatear(r, op.res_unidad)
                ok = math.isclose(r, esperado, rel_tol=1e-6, abs_tol=1e-9)
            except ErrorCalculo as e:
                calc, ok = str(e), False
            correctos += ok
            ent = "; ".join(f"{k}={v}" for k, v in entradas.items()
                            if k not in ("perA", "perB", "tipoA", "tipoB"))
            self.tv_val.insert("", "end", tags=("ok" if ok else "mal",), values=(
                self.nombre_mod[op.modulo], op.titulo, ent,
                formatear(esperado, op.res_unidad), calc, "Correcto" if ok else "Difiere"))
        total = len(EJERCICIOS)
        self.var_validados.set(f"{correctos} / {total}")

    # ---------------------------------------------------------------- reporte
    def _crear_reporte(self):
        marco = tk.Frame(self.cuerpo, bg=C["fondo"])
        self._registrar_pagina("reporte", marco, "Reporte",
                               "Historial de los cálculos realizados en esta sesión.")
        barra = tk.Frame(marco, bg=C["fondo"])
        barra.pack(fill="x", pady=(0, 10), padx=(0, 14))
        self.lbl_rep = tk.Label(barra, text="Todavía no hay cálculos", font=F(11, "bold"),
                                fg=C["suave"], bg=C["fondo"])
        self.lbl_rep.pack(side="left")
        Boton(barra, "Limpiar", self.limpiar_historial, "secundario").pack(side="right")
        Boton(barra, "Exportar TXT", lambda: self.exportar("txt"), "claro").pack(side="right", padx=8)
        Boton(barra, "Exportar CSV", lambda: self.exportar("csv")).pack(side="right")

        caja = Tarjeta(marco)
        caja.pack(fill="both", expand=True, padx=(0, 14), pady=(0, 14))
        cols = ("hora", "modulo", "operacion", "entradas", "resultado")
        self.tv_rep = ttk.Treeview(caja, columns=cols, show="headings")
        for c, t, w in zip(cols, ("Hora", "Módulo", "Operación", "Entradas", "Resultado"),
                           (75, 120, 170, 300, 160)):
            self.tv_rep.heading(c, text=t)
            self.tv_rep.column(c, width=w, minwidth=60, anchor="w")
        sb = ttk.Scrollbar(caja, orient="vertical", command=self.tv_rep.yview)
        self.tv_rep.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tv_rep.pack(side="left", fill="both", expand=True, padx=1, pady=1)

    def _actualizar_contador(self):
        n = len(self.historial)
        if n == 0:
            self.lbl_rep.configure(text="Todavía no hay cálculos", fg=C["suave"])
        else:
            self.lbl_rep.configure(text=f"{n} cálculo{'s' if n != 1 else ''} en esta sesión", fg=C["texto"])

    def registrar(self, op, entradas, resultado):
        ent = "; ".join(f"{c.etiqueta}={entradas[c.clave]}" for c in op.campos
                        if str(entradas.get(c.clave, "")).strip())
        fila = (datetime.datetime.now().strftime("%H:%M:%S"), self.nombre_mod[op.modulo],
                op.titulo, ent, resultado)
        self.historial.append(fila)
        self.tv_rep.insert("", "end", values=fila)
        self.tv_rep.yview_moveto(1)
        self._actualizar_contador()

    def limpiar_historial(self):
        self.historial.clear()
        self.tv_rep.delete(*self.tv_rep.get_children())
        self._actualizar_contador()

    def exportar(self, formato):
        if not self.historial:
            messagebox.showinfo("Reporte", "Todavía no hay cálculos para exportar.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension="." + formato, initialfile="reporte_calculos." + formato,
            filetypes=[("CSV" if formato == "csv" else "Texto", "*." + formato)])
        if not ruta:
            return
        if formato == "csv":
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(["Hora", "Módulo", "Operación", "Entradas", "Resultado"])
                w.writerows(self.historial)
        else:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("REPORTE | CALCULADORA FINANCIERA\n" + "=" * 60 + "\n")
                for h, m, o, e, r in self.historial:
                    f.write(f"[{h}] {m} - {o}\n    Entradas: {e}\n    Resultado: {r}\n\n")
        messagebox.showinfo("Reporte", "Reporte guardado correctamente.")


if __name__ == "__main__":
    App().mainloop()
