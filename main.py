
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


class MeuAplicativo(App):

    def build(self):
        tela = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        titulo = Label(
            text="MEU PRIMEIRO APP",
            font_size="26sp"
        )

        mensagem = Label(
            text="Aplicativo criado em Python!",
            font_size="18sp"
        )

        botao = Button(
            text="INICIAR",
            size_hint=(1, 0.2),
            font_size="20sp"
        )

        botao.bind(
            on_press=self.iniciar
        )

        tela.add_widget(titulo)
        tela.add_widget(mensagem)
        tela.add_widget(botao)

        return tela

    def iniciar(self, instance):
        instance.text = "APLICATIVO FUNCIONANDO!"


if __name__ == "__main__":
    MeuAplicativo().run()
  
