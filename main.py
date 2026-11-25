import json
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget


MESES = [
    "Agosto / 2026",
    "Setembro / 2026",
    "Outubro / 2026",
    "Novembro / 2026",
    "Dezembro / 2026",
    "Janeiro / 2027",
    "Fevereiro / 2027",
    "Março / 2027",
    "Abril / 2027",
    "Maio / 2027",
    "Junho / 2027",
    "Julho / 2027",
    "Agosto / 2027",
    "Setembro / 2027",
    "Outubro / 2027",
    "Novembro / 2027",
    "Dezembro / 2027",
]


def _parse_numero(texto):
    if not texto:
        return None
    limpo = texto.strip().replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return None


def _fmt_virgula(valor, decimais=2):
    return f"{valor:.{decimais}f}".replace(".", ",")


class ControleFreteApp(App):
    def build(self):
        Window.clearcolor = (0.043, 0.051, 0.067, 1)

        self.mes_atual = "Novembro / 2026"
        self.media_pedida = 2.0
        self.indice_editando = None
        self.tipo_viagem = "carregado"
        self.avancado_aberto = False
        self.dados = {mes: {"viagens": [], "diesel": []} for mes in MESES}
        self._inputs = []

        self._carregar_dados()

        raiz = ScrollView(do_scroll_x=False, do_scroll_y=True)

        faixa_externa = BoxLayout(
            orientation="horizontal",
            padding=[dp(16), dp(16), dp(16), dp(36)],
            size_hint_y=None,
        )
        faixa_externa.bind(minimum_height=faixa_externa.setter("height"))

        self._esq_spacer = Widget(size_hint_x=None, width=0)
        self._dir_spacer = Widget(size_hint_x=None, width=0)

        self.container = BoxLayout(
            orientation="vertical",
            spacing=dp(14),
            size_hint_y=None,
        )
        self.container.bind(minimum_height=self.container.setter("height"))
        Window.bind(size=self._ajustar_largura_central)
        Window.bind(on_focus=self._ao_ganhar_foco_janela)

        faixa_externa.add_widget(self._esq_spacer)
        faixa_externa.add_widget(self.container)
        faixa_externa.add_widget(self._dir_spacer)

        self.container.add_widget(Widget(size_hint_y=None, height=dp(24)))

        titulo = Label(
            text="Controle de Frete",
            font_size=sp(20),
            bold=True,
            color=(0.945, 0.953, 0.961, 1),
            size_hint_y=None,
            height=dp(36),
        )
        self.container.add_widget(titulo)

        # Card: Mês de Referência
        card_mes = self._criar_bloco(
            padding=[dp(14), dp(14), dp(14), dp(14)], spacing=dp(8)
        )
        card_mes.add_widget(self._criar_titulo_card("MÊS DE REFERÊNCIA"))

        self.spinner_mes = Spinner(
            text=self.mes_atual,
            values=MESES,
            size_hint_y=None,
            height=dp(44),
            font_size=sp(14),
            background_normal="",
            background_color=(0.110, 0.140, 0.200, 1),
            color=(0.945, 0.953, 0.961, 1),
        )
        self.spinner_mes.bind(text=self.ao_mudar_mes)
        card_mes.add_widget(self.spinner_mes)
        self.container.add_widget(card_mes)

        # Card: Resumo do Mês
        card_resumo = self._criar_bloco(
            padding=[dp(14), dp(14), dp(14), dp(14)], spacing=dp(8)
        )
        card_resumo.add_widget(self._criar_titulo_card("RESUMO DO MÊS"))

        grid = GridLayout(
            cols=2, spacing=[dp(8), dp(6)], size_hint_y=None, height=dp(186)
        )
        self.lbl_fat_valor = self._criar_linha_resumo(
            grid, "Total Faturado:", "R$ 0.00", (0.063, 0.725, 0.506, 1)
        )
        self.lbl_km_total_valor = self._criar_linha_resumo(
            grid, "KM Total Rodado:", "0 km", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_km_carr_valor = self._criar_linha_resumo(
            grid, "KM Carregado:", "0 km", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_km_vazio_valor = self._criar_linha_resumo(
            grid, "KM Vazio:", "0 km", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_diesel_valor = self._criar_linha_resumo(
            grid, "Diesel Abastecido:", "0.00 L", (0.220, 0.741, 0.973, 1)
        )
        self.lbl_media_valor = self._criar_linha_resumo(
            grid, "Média Geral (KM/L):", "0,00 KM/L", (0.220, 0.741, 0.973, 1)
        )
        card_resumo.add_widget(grid)
        self.container.add_widget(card_resumo)

        # Card: Nova Viagem / Trecho
        card_viagem = self._criar_bloco(
            padding=[dp(14), dp(14), dp(14), dp(14)], spacing=dp(8)
        )
        card_viagem.add_widget(self._criar_titulo_card("NOVA VIAGEM / TRECHO"))

        card_viagem.add_widget(self._criar_rotulo("Rota / Descrição"))
        self.input_rota = self._criar_input("Ex: Sorriso para Paranaguá")
        card_viagem.add_widget(self.input_rota)

        box_tipo = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(42))
        self.btn_tipo_carr = ToggleButton(
            text="Carregado",
            group="tipo_viagem",
            state="down",
            bold=True,
            font_size=sp(14),
            background_normal="",
            background_color=(0.145, 0.388, 0.922, 1),
        )
        self.btn_tipo_vazio = ToggleButton(
            text="Vazio",
            group="tipo_viagem",
            state="normal",
            bold=True,
            font_size=sp(14),
            background_normal="",
            background_color=(0.200, 0.255, 0.333, 1),
        )
        self.btn_tipo_carr.bind(on_press=lambda *_: self._set_tipo("carregado"))
        self.btn_tipo_vazio.bind(on_press=lambda *_: self._set_tipo("vazio"))
        box_tipo.add_widget(self.btn_tipo_carr)
        box_tipo.add_widget(self.btn_tipo_vazio)
        card_viagem.add_widget(box_tipo)

        box_km = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(70))
        col_ini = BoxLayout(orientation="vertical", spacing=dp(4))
        col_ini.add_widget(self._criar_rotulo("KM Início"))
        self.input_km_ini = self._criar_input("0", input_filter="float")
        col_ini.add_widget(self.input_km_ini)

        col_fim = BoxLayout(orientation="vertical", spacing=dp(4))
        col_fim.add_widget(self._criar_rotulo("KM Fim"))
        self.input_km_fim = self._criar_input("0", input_filter="float")
        col_fim.add_widget(self.input_km_fim)

        box_km.add_widget(col_ini)
        box_km.add_widget(col_fim)
        card_viagem.add_widget(box_km)

        card_viagem.add_widget(self._criar_rotulo("Faturamento (R$)"))
        self.input_fat = self._criar_input("0.00", input_filter="float")
        card_viagem.add_widget(self.input_fat)

        self.lbl_aviso = Label(
            text="",
            font_size=sp(12.5),
            color=(0.988, 0.647, 0.647, 1),
            size_hint_y=None,
            height=dp(22),
        )
        card_viagem.add_widget(self.lbl_aviso)

        self.btn_salvar_viagem = Button(
            text="Salvar Viagem",
            size_hint_y=None,
            height=dp(46),
            font_size=sp(15),
            bold=True,
            background_normal="",
            background_color=(0.145, 0.388, 0.922, 1),
            color=(1, 1, 1, 1),
        )
        self.btn_salvar_viagem.bind(on_press=self.salvar_viagem)
        card_viagem.add_widget(self.btn_salvar_viagem)

        self.container.add_widget(card_viagem)

        # Card: Abastecimento de Diesel
        card_diesel = self._criar_bloco(
            padding=[dp(14), dp(14), dp(14), dp(14)], spacing=dp(8)
        )
        card_diesel.add_widget(
            self._criar_titulo_card("REGISTRAR ABASTECIMENTO DE DIESEL")
        )
        card_diesel.add_widget(self._criar_rotulo("Litros Abastecidos"))
        self.input_diesel = self._criar_input("Ex: 450.5", input_filter="float")
        card_diesel.add_widget(self.input_diesel)

        btn_diesel = Button(
            text="Adicionar Diesel",
            size_hint_y=None,
            height=dp(44),
            font_size=sp(14.5),
            bold=True,
            background_normal="",
            background_color=(0.200, 0.255, 0.333, 1),
            color=(1, 1, 1, 1),
        )
        btn_diesel.bind(on_press=self.salvar_diesel)
        card_diesel.add_widget(btn_diesel)
        self.container.add_widget(card_diesel)

        # Card: Histórico de Lançamentos + Fechamento
        self.card_historico = self._criar_bloco(
            padding=[dp(14), dp(14), dp(14), dp(14)], spacing=dp(8)
        )
        self.card_historico.add_widget(
            self._criar_titulo_card("HISTÓRICO DE LANÇAMENTOS")
        )

        self.box_historico = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(32),
        )
        self.box_historico.bind(minimum_height=self.box_historico.setter("height"))
        self.card_historico.add_widget(self.box_historico)

        self.btn_resumo_relatorio = Button(
            text="Ver Fechamento do Mês",
            size_hint_y=None,
            height=dp(46),
            font_size=sp(14.5),
            bold=True,
            background_normal="",
            background_color=(0.063, 0.725, 0.506, 1),
            color=(1, 1, 1, 1),
        )
        self.btn_resumo_relatorio.bind(on_press=self.abrir_relatorio_mes)
        self.card_historico.add_widget(self.btn_resumo_relatorio)

        self.container.add_widget(self.card_historico)

        # Card: Cálculo Avançado de Desempenho
        self.card_avancado = self._criar_bloco(
            padding=[dp(14), dp(14), dp(14), dp(14)],
            spacing=dp(8),
            cor_fundo=(0.059, 0.071, 0.098, 1),
        )

        self.btn_toggle_avancado = Button(
            text="[+] Cálculo Avançado de Desempenho",
            size_hint_y=None,
            height=dp(44),
            font_size=sp(13.5),
            bold=True,
            background_normal="",
            background_color=(0.118, 0.149, 0.212, 1),
            color=(0.850, 0.880, 0.920, 1),
        )
        self.btn_toggle_avancado.bind(on_press=self.alternar_avancado)
        self.card_avancado.add_widget(self.btn_toggle_avancado)

        self.box_corpo_avancado = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            height=0,
            opacity=0,
        )

        self.box_corpo_avancado.add_widget(self._criar_rotulo("Média Pedida (Base)"))
        self.input_media_pedida = self._criar_input("2.0", input_filter="float")
        self.input_media_pedida.text = str(self.media_pedida)
        self.input_media_pedida.bind(text=self.ao_alterar_media_pedida)
        self.box_corpo_avancado.add_widget(self.input_media_pedida)

        grid_av = GridLayout(
            cols=2, spacing=[dp(6), dp(6)], size_hint_y=None, height=dp(135)
        )
        self.lbl_porc_carr = self._criar_linha_resumo(
            grid_av, "% Carregado:", "0,0%", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_meta_aj = self._criar_linha_resumo(
            grid_av, "Média Meta:", "0,00", (0.945, 0.953, 0.961, 1)
        )
        self.lbl_media_real_av = self._criar_linha_resumo(
            grid_av, "Média Real:", "0,00", (0.220, 0.741, 0.973, 1)
        )
        self.lbl_media_equiv = self._criar_linha_resumo(
            grid_av, "Média Equivalente:", "0,00", (0.961, 0.620, 0.043, 1)
        )
        self.lbl_status_meta = self._criar_linha_resumo(
            grid_av,
            "Situação vs Meta:",
            "Aguardando diesel",
            (0.580, 0.639, 0.722, 1),
        )
        self.box_corpo_avancado.add_widget(grid_av)

        self.card_avancado.add_widget(self.box_corpo_avancado)
        self.container.add_widget(self.card_avancado)

        self.container.add_widget(Widget(size_hint_y=None, height=dp(28)))
        raiz.add_widget(faixa_externa)

        self._ajustar_largura_central()
        self.atualizar_tudo()
        return raiz

    def on_resume(self):
        Clock.schedule_once(lambda *_: self._resetar_foco_inputs(), 0.05)

    def _ao_ganhar_foco_janela(self, window, focused):
        if focused:
            Clock.schedule_once(lambda *_: self._resetar_foco_inputs(), 0.05)

    def _resetar_foco_inputs(self):
        for campo in self._inputs:
            campo.focus = False

    def _criar_bloco(self, padding, spacing, cor_fundo=(0.071, 0.086, 0.118, 1)):
        bloco = BoxLayout(
            orientation="vertical",
            padding=padding,
            spacing=spacing,
            size_hint_y=None,
        )
        bloco.bind(minimum_height=bloco.setter("height"))
        with bloco.canvas.before:
            Color(*cor_fundo)
            rect = Rectangle(pos=bloco.pos, size=bloco.size)
        bloco.bind(
            pos=lambda inst, val, r=rect: setattr(r, "pos", val),
            size=lambda inst, val, r=rect: setattr(r, "size", val),
        )
        return bloco

    def _ajustar_largura_central(self, *args):
        largura_util = max(dp(240), Window.width - dp(32))
        largura_alvo = min(largura_util, dp(420))
        sobra = max(0.0, (largura_util - largura_alvo) / 2.0)
        self._esq_spacer.width = sobra
        self._dir_spacer.width = sobra
        self.container.width = largura_alvo

    def _caminho_arquivo_dados(self):
        return os.path.join(self.user_data_dir, "controle_frete_dados.json")

    def _carregar_dados(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        caminho = self._caminho_arquivo_dados()
        if not os.path.exists(caminho):
            return
        try:
            with open(caminho, "r", encoding="utf-8") as arq:
                conteudo = json.load(arq)
            if isinstance(conteudo, dict):
                if conteudo.get("mes_atual") in MESES:
                    self.mes_atual = conteudo["mes_atual"]
                if conteudo.get("media_pedida") is not None:
                    self.media_pedida = float(conteudo["media_pedida"])
                salvos = conteudo.get("meses", {})
                for mes in MESES:
                    item = salvos.get(mes, {})
                    self.dados[mes] = {
                        "viagens": list(item.get("viagens", [])),
                        "diesel": list(item.get("diesel", [])),
                    }
        except Exception:
            pass

    def _salvar_dados(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        caminho = self._caminho_arquivo_dados()
        payload = {
            "mes_atual": self.mes_atual,
            "media_pedida": self.media_pedida,
            "meses": self.dados,
        }
        try:
            with open(caminho, "w", encoding="utf-8") as arq:
                json.dump(payload, arq, ensure_ascii=False, indent=2)
        except Exception as e:
            self.lbl_aviso.text = f"Erro ao salvar: {e}"

    def _criar_titulo_card(self, texto):
        lbl = Label(
            text=texto,
            font_size=sp(12),
            bold=True,
            color=(0.560, 0.600, 0.665, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _criar_rotulo(self, texto):
        lbl = Label(
            text=texto,
            font_size=sp(13),
            color=(0.740, 0.775, 0.825, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(19),
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def _criar_input(self, hint, input_filter=None):
        campo = TextInput(
            hint_text=hint,
            input_filter=input_filter,
            multiline=False,
            font_size=sp(14.5),
            size_hint_y=None,
            height=dp(46),
            background_color=(0.140, 0.175, 0.235, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.680, 0.730, 0.800, 1),
            cursor_color=(0.220, 0.741, 0.973, 1),
            cursor_width=dp(2.5),
            padding=[dp(12), dp(12)],
        )
        self._inputs.append(campo)
        return campo

    def _criar_linha_resumo(self, grid, rotulo, inicial, cor_valor):
        lbl_nome = Label(
            text=rotulo,
            font_size=sp(13.5),
            color=(0.640, 0.680, 0.740, 1),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(25),
        )
        lbl_nome.bind(size=lbl_nome.setter("text_size"))

        lbl_val = Label(
            text=inicial,
            font_size=sp(13.5),
            bold=True,
            color=cor_valor,
            halign="right",
            valign="middle",
            size_hint_y=None,
            height=dp(25),
        )
        lbl_val.bind(size=lbl_val.setter("text_size"))

        grid.add_widget(lbl_nome)
        grid.add_widget(lbl_val)
        return lbl_val

    def _set_tipo(self, tipo):
        self._resetar_foco_inputs()
        self.tipo_viagem = tipo
        if tipo == "carregado":
            self.btn_tipo_carr.state = "down"
            self.btn_tipo_vazio.state = "normal"
        else:
            self.btn_tipo_carr.state = "normal"
            self.btn_tipo_vazio.state = "down"

    def _limpar_form_viagem(self):
        self.indice_editando = None
        self.input_rota.text = ""
        self.input_km_ini.text = ""
        self.input_km_fim.text = ""
        self.input_fat.text = ""
        self._set_tipo("carregado")
        self.btn_salvar_viagem.text = "Salvar Viagem"

    def alternar_avancado(self, instance):
        self._resetar_foco_inputs()
        self.avancado_aberto = not self.avancado_aberto
        if self.avancado_aberto:
            self.box_corpo_avancado.height = dp(206)
            self.box_corpo_avancado.opacity = 1
            self.btn_toggle_avancado.text = "[-] Cálculo Avançado de Desempenho"
        else:
            self.box_corpo_avancado.height = 0
            self.box_corpo_avancado.opacity = 0
            self.btn_toggle_avancado.text = "[+] Cálculo Avançado de Desempenho"

    def ao_alterar_media_pedida(self, instance, valor_texto):
        parsed = _parse_numero(valor_texto)
        if parsed is not None and parsed >= 0:
            self.media_pedida = parsed
            self.atualizar_tudo()

    def ao_mudar_mes(self, spinner, texto_mes):
        self._resetar_foco_inputs()
        self.mes_atual = texto_mes
        self.lbl_aviso.text = ""
        self._limpar_form_viagem()
        self.atualizar_tudo()

    def salvar_viagem(self, instance):
        self._resetar_foco_inputs()
        rota = self.input_rota.text.strip()
        km_ini = _parse_numero(self.input_km_ini.text)
        km_fim = _parse_numero(self.input_km_fim.text)
        fat = _parse_numero(self.input_fat.text)
        if fat is None:
            fat = 0.0

        if not rota or km_ini is None or km_fim is None:
            self.lbl_aviso.text = "Preencha a Rota, KM Início e KM Fim."
            return

        if km_fim < km_ini:
            self.lbl_aviso.text = "KM Fim não pode ser menor que KM Início."
            return

        self.lbl_aviso.text = ""
        viagens = self.dados[self.mes_atual]["viagens"]
        item = {
            "rota": rota,
            "tipo": self.tipo_viagem,
            "km_inicio": km_ini,
            "km_fim": km_fim,
            "faturamento": fat,
        }

        if self.indice_editando is not None and 0 <= self.indice_editando < len(
            viagens
        ):
            viagens[self.indice_editando] = item
        else:
            viagens.append(item)

        self._limpar_form_viagem()
        self.atualizar_tudo()

    def salvar_diesel(self, instance):
        self._resetar_foco_inputs()
        litros = _parse_numero(self.input_diesel.text)
        if litros is None or litros <= 0:
            self.lbl_aviso.text = "Informe a quantidade de litros de diesel."
            return

        self.lbl_aviso.text = ""
        self.dados[self.mes_atual]["diesel"].append({"litros": litros})
        self.input_diesel.text = ""
        self.atualizar_tudo()

    def iniciar_edicao(self, idx):
        self._resetar_foco_inputs()
        viagens = self.dados[self.mes_atual]["viagens"]
        if not (0 <= idx < len(viagens)):
            return
        v = viagens[idx]
        self.indice_editando = idx
        self.lbl_aviso.text = ""
        self.input_rota.text = str(v.get("rota", ""))
        self.input_km_ini.text = str(v.get("km_inicio", ""))
        self.input_km_fim.text = str(v.get("km_fim", ""))
        self.input_fat.text = str(v.get("faturamento", ""))
        self._set_tipo(v.get("tipo", "carregado"))
        self.btn_salvar_viagem.text = "Salvar Alteração"

    def excluir_item(self, categoria, idx):
        self._resetar_foco_inputs()
        lista = self.dados[self.mes_atual][categoria]
        if not (0 <= idx < len(lista)):
            return
        if categoria == "viagens" and self.indice_editando == idx:
            self._limpar_form_viagem()
        lista.pop(idx)
        self.atualizar_tudo()

    def _calcular_metricas_mes(self, mes_data):
        fat_total = 0.0
        km_carr = 0.0
        km_vazio = 0.0
        total_litros = 0.0

        for v in mes_data["viagens"]:
            dist = max(
                0.0, float(v.get("km_fim", 0)) - float(v.get("km_inicio", 0))
            )
            fat_total += float(v.get("faturamento", 0))
            if v.get("tipo") == "vazio":
                km_vazio += dist
            else:
                km_carr += dist

        for d in mes_data["diesel"]:
            total_litros += float(d.get("litros", 0))

        km_total = km_carr + km_vazio
        media_real = (km_total / total_litros) if total_litros > 0 else 0.0

        media_pedida = self.media_pedida
        porc_carr = (km_carr / km_total) * 100.0 if km_total > 0 else 0.0
        porc_menos_50 = porc_carr - 50.0
        media_meta = (
            (media_pedida - (porc_menos_50 * 0.014))
            if km_total > 0
            else media_pedida
        )

        media_equiv = media_pedida
        status_texto = "Aguardando diesel"
        status_cor = (0.580, 0.639, 0.722, 1)

        if total_litros > 0 and media_meta > 0:
            media_equiv = media_pedida * (media_real / media_meta)
            diff_meta = media_real - media_meta
            diff_base = media_equiv - media_pedida
            sinal_base = "+" if diff_base >= 0 else ""

            if diff_meta >= 0:
                status_texto = f"ACIMA DA META ({sinal_base}{_fmt_virgula(diff_base)})"
                status_cor = (0.063, 0.725, 0.506, 1)
            else:
                status_texto = f"ABAIXO DA META ({sinal_base}{_fmt_virgula(diff_base)})"
                status_cor = (0.973, 0.443, 0.443, 1)

        return {
            "fat_total": fat_total,
            "km_total": km_total,
            "km_carr": km_carr,
            "km_vazio": km_vazio,
            "total_litros": total_litros,
            "media_real": media_real,
            "porc_carr": porc_carr,
            "media_meta": media_meta,
            "media_equiv": media_equiv,
            "status_texto": status_texto,
            "status_cor": status_cor,
        }

    def abrir_relatorio_mes(self, instance):
        self._resetar_foco_inputs()
        m = self._calcular_metricas_mes(self.dados[self.mes_atual])
        texto = (
            f"Mês: {self.mes_atual}\n"
            f"Total Faturado: R$ {_fmt_virgula(m['fat_total'])}\n"
            f"KM Total: {m['km_total']:.0f} km\n"
            f"KM Carregado: {m['km_carr']:.0f} km ({_fmt_virgula(m['porc_carr'], 1)}%)\n"
            f"KM Vazio: {m['km_vazio']:.0f} km\n"
            f"Diesel: {_fmt_virgula(m['total_litros'])} L\n"
            f"Média Real: {_fmt_virgula(m['media_real'])} KM/L\n"
            f"Média Meta: {_fmt_virgula(m['media_meta'])} KM/L\n"
            f"Média Equivalente: {_fmt_virgula(m['media_equiv'])} KM/L\n"
            f"Situação: {m['status_texto']}"
        )

        conteudo_popup = BoxLayout(
            orientation="vertical", padding=dp(16), spacing=dp(12)
        )
        lbl = Label(
            text=texto,
            font_size=sp(14),
            halign="left",
            valign="middle",
        )
        lbl.bind(size=lbl.setter("text_size"))

        btn_fechar = Button(
            text="Fechar",
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=(0.145, 0.388, 0.922, 1),
            bold=True,
        )
        conteudo_popup.add_widget(lbl)
        conteudo_popup.add_widget(btn_fechar)

        popup = Popup(
            title=f"Fechamento - {self.mes_atual}",
            content=conteudo_popup,
            size_hint=(0.9, 0.72),
            background_color=(0.082, 0.098, 0.133, 1),
        )
        btn_fechar.bind(on_press=popup.dismiss)
        popup.open()

    def _construir_historico(self, mes_data):
        self.box_historico.clear_widgets()
        viagens = mes_data["viagens"]
        diesels = mes_data["diesel"]

        if not viagens and not diesels:
            vazio = Label(
                text="Nenhum lançamento neste mês.",
                font_size=sp(13),
                color=(0.450, 0.500, 0.580, 1),
                size_hint_y=None,
                height=dp(30),
            )
            self.box_historico.add_widget(vazio)
            return

        for idx, v in enumerate(viagens):
            dist = max(
                0.0, float(v.get("km_fim", 0)) - float(v.get("km_inicio", 0))
            )
            fat = float(v.get("faturamento", 0))
            tipo = v.get("tipo", "carregado")

            linha = BoxLayout(
                orientation="horizontal",
                padding=[dp(10), dp(8)],
                spacing=dp(8),
                size_hint_y=None,
                height=dp(70),
            )
            with linha.canvas.before:
                Color(0.055, 0.067, 0.094, 1)
                rect = Rectangle(pos=linha.pos, size=linha.size)
            linha.bind(
                pos=lambda inst, val, r=rect: setattr(r, "pos", val),
                size=lambda inst, val, r=rect: setattr(r, "size", val),
            )

            info = Label(
                text=f"[Viagem] {v.get('rota', '')}\nTipo: {tipo} | KM: {dist:.0f} km | Fat: R$ {_fmt_virgula(fat)}",
                font_size=sp(12),
                color=(0.560, 0.820, 0.980, 1),
                halign="left",
                valign="middle",
            )
            info.bind(size=info.setter("text_size"))

            btn_edit = Button(
                text="Editar",
                size_hint=(None, None),
                size=(dp(68), dp(40)),
                font_size=sp(12.5),
                bold=True,
                background_normal="",
                background_color=(0.145, 0.388, 0.922, 1),
                color=(1, 1, 1, 1),
                pos_hint={"center_y": 0.5},
            )
            btn_edit.bind(on_press=lambda _, i=idx: self.iniciar_edicao(i))

            btn_del = Button(
                text="Excluir",
                size_hint=(None, None),
                size=(dp(70), dp(40)),
                font_size=sp(12.5),
                bold=True,
                background_normal="",
                background_color=(0.860, 0.240, 0.240, 1),
                color=(1, 1, 1, 1),
                pos_hint={"center_y": 0.5},
            )
            btn_del.bind(on_press=lambda _, i=idx: self.excluir_item("viagens", i))

            linha.add_widget(info)
            linha.add_widget(btn_edit)
            linha.add_widget(btn_del)
            self.box_historico.add_widget(linha)

        for idx, d in enumerate(diesels):
            litros = float(d.get("litros", 0))
            linha_d = BoxLayout(
                orientation="horizontal",
                padding=[dp(10), dp(8)],
                spacing=dp(8),
                size_hint_y=None,
                height=dp(60),
            )
            with linha_d.canvas.before:
                Color(0.055, 0.067, 0.094, 1)
                rect_d = Rectangle(pos=linha_d.pos, size=linha_d.size)
            linha_d.bind(
                pos=lambda inst, val, r=rect_d: setattr(r, "pos", val),
                size=lambda inst, val, r=rect_d: setattr(r, "size", val),
            )

            info_d = Label(
                text=f"[Abastecimento Diesel]\nLitros: {_fmt_virgula(litros)} L",
                font_size=sp(12),
                color=(0.961, 0.620, 0.043, 1),
                halign="left",
                valign="middle",
            )
            info_d.bind(size=info_d.setter("text_size"))

            btn_del_d = Button(
                text="Excluir",
                size_hint=(None, None),
                size=(dp(70), dp(40)),
                font_size=sp(12.5),
                bold=True,
                background_normal="",
                background_color=(0.860, 0.240, 0.240, 1),
                color=(1, 1, 1, 1),
                pos_hint={"center_y": 0.5},
            )
            btn_del_d.bind(on_press=lambda _, i=idx: self.excluir_item("diesel", i))

            linha_d.add_widget(info_d)
            linha_d.add_widget(btn_del_d)
            self.box_historico.add_widget(linha_d)

    def atualizar_tudo(self):
        mes_data = self.dados[self.mes_atual]
        m = self._calcular_metricas_mes(mes_data)

        self.lbl_fat_valor.text = f"R$ {m['fat_total']:.2f}"
        self.lbl_km_total_valor.text = f"{m['km_total']:.0f} km"
        self.lbl_km_carr_valor.text = f"{m['km_carr']:.0f} km"
        self.lbl_km_vazio_valor.text = f"{m['km_vazio']:.0f} km"
        self.lbl_diesel_valor.text = f"{m['total_litros']:.2f} L"
        self.lbl_media_valor.text = f"{_fmt_virgula(m['media_real'])} KM/L"

        self.lbl_porc_carr.text = f"{_fmt_virgula(m['porc_carr'], 1)}%"
        self.lbl_meta_aj.text = _fmt_virgula(m["media_meta"])
        self.lbl_media_real_av.text = _fmt_virgula(m["media_real"])
        self.lbl_media_equiv.text = _fmt_virgula(m["media_equiv"])
        self.lbl_status_meta.text = m["status_texto"]
        self.lbl_status_meta.color = m["status_cor"]

        self._construir_historico(mes_data)
        self._salvar_dados()


if __name__ == "__main__":
    ControleFreteApp().run()
