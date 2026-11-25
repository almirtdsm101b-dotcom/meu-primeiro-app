
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.window import Window

class MeuAplicativo(App):

    def build(self):
        tela = BoxLayout(
            orientation="vertical",
            padding=[25, 40, 25, 40],
            spacing=15
        )

        tela.add_widget(Widget())

        titulo = Label(
            text="MEU PRIMEIRO APP",
            font_size="23sp",
            size_hint=(1, None),
            height=55
        )

        mensagem = Label(
            text="Aplicativo criado em Python!",
            font_size="16sp",
            size_hint=(1, None),
            height=45
        )

        botao = Button(
            text="INICIAR",
            font_size="18sp",
            size_hint=(0.75, None),
            height=55,
            pos_hint={"center_x": 0.5}
        )

        botao.bind(on_press=self.iniciar)

        tela.add_widget(titulo)
        tela.add_widget(mensagem)
        tela.add_widget(botao)

        tela.add_widget(Widget())

        return tela

    def iniciar(self, instance):
        instance.text = "APLICATIVO FUNCIONANDO!"

if __name__ == "__main__":
    MeuAplicativo().run()
    
