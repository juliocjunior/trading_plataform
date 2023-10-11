import sys
import requests
import pandas as pd
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QPushButton, QLineEdit, QListWidget, QLabel, QStatusBar
from PyQt5.QtCore import Qt, QTimer
from PyQt5.uic import loadUi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class Acao:
    def __init__(self, nome, preco, volume):
        self.nome = nome # O nome da ação (ex: PETR4)
        self.preco = preco # O preço atual da ação (ex: 25.50)
        self.volume = volume # O volume negociado da ação (ex: 1000000)

class Ordem:
    def __init__(self, acao, quantidade, tipo):
        self.acao = acao # Uma instância de Acao
        self.quantidade = quantidade # A quantidade de ações que se deseja comprar ou vender (ex: 100)
        self.tipo = tipo # O tipo da ordem (compra ou venda)
        self.status = "aberta" # O status da ordem (aberta ou fechada)
        self.preco = None # O preço de execução da ordem (None se ainda não foi executada)

    def validar(self):
        # Esta função verifica se a ordem é válida (se há saldo suficiente para comprar ou se há ações suficientes para vender)
        if self.tipo == "compra":
            if saldo >= self.quantidade * self.acao.preco:
                return True
            else:
                return False
        elif self.tipo == "venda":
            if carteira.get(self.acao.nome, 0) >= self.quantidade:
                return True
            else:
                return False

    def executar(self):
        # Esta função executa a ordem na corretora fictícia (que pode ser simulada com uma lista ou um dicionário)
        if self.validar():
            self.status = "fechada"
            self.preco = self.acao.preco
            if self.tipo == "compra":
                saldo -= self.quantidade * self.preco
                carteira[self.acao.nome] = carteira.get(self.acao.nome, 0) + self.quantidade
            elif self.tipo == "venda":
                saldo += self.quantidade * self.preco
                carteira[self.acao.nome] -= self.quantidade

    def cancelar(self):
        # Esta função cancela a ordem na corretora fictícia (se ela ainda estiver aberta)
        if self.status == "aberta":
            self.status = "cancelada"

    def calcular_resultado(self):
        # Esta função calcula o resultado da operação (lucro ou prejuízo) (se ela estiver fechada)
        if self.status == "fechada":
            if self.tipo == "compra":
                return (self.acao.preco - self.preco) * self.quantidade
            elif self.tipo == "venda":
                return (self.preco - self.acao.preco) * self.quantidade

saldo = 10000 # O saldo inicial do usuário (em reais)
carteira = {} # A carteira do usuário (um dicionário que mapeia o nome da ação para a quantidade possuída)

def calcular_indicadores(df):
    # Esta função recebe um dataframe com os dados históricos da ação e calcula os indicadores técnicos que serão usados para auxiliar nas decisões de compra ou venda, como médias móveis, bandas de Bollinger, MACD, etc. Essa função retorna um dataframe com os valores dos indicadores para cada data.
    df["MM20"] = df["fechamento"].rolling(20).mean() # Média móvel de 20 períodos
    df["MM50"] = df["fechamento"].rolling(50).mean() # Média móvel de 50 períodos
    df["Banda_superior"] = df["MM20"] + 2 * df["fechamento"].rolling(20).std() # Banda superior de Bollinger
    df["Banda_inferior"] = df["MM20"] - 2 * df["fechamento"].rolling(20).std() # Banda inferior de Bollinger
    df["EMA12"] = df["fechamento"].ewm(span=12).mean() # Média móvel exponencial de 12 períodos
    df["EMA26"] = df["fechamento"].ewm(span=26).mean() # Média móvel exponencial de 26 períodos
    df["MACD"] = df["EMA12"] - df["EMA26"] # Diferença entre as médias móveis exponenciais
    df["Sinal"] = df["MACD"].ewm(span=9).mean() # Média móvel exponencial de 9 períodos do MACD
    df["Histograma"] = df["MACD"] - df["Sinal"] # Diferença entre o MACD e o sinal
    return df

def get_historico(symbol, interval):
    # Esta função faz uma requisição para a API de dados financeiros usando a biblioteca requests, e retorna um dataframe com os dados históricos da ação selecionada na tabela, com as colunas data, abertura, maxima, minima, fechamento e volume.
    url = f"https://api.bing.com/finance/historical?symbol={symbol}&interval={interval}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df.columns = ["data", "abertura", "maxima", "minima", "fechamento", "volume"]
    return df

def plot_candlestick(df, title):
    # Esta função recebe um dataframe com os dados históricos da ação e um título, e plota um gráfico de candlestick na interface gráfica usando a biblioteca matplotlib.
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_title(title)
    ax.set_xlabel("Data")
    ax.set_ylabel("Preço")
    ax.grid()
    ax.plot(df["data"], df["fechamento"], color="black", label="Fechamento")
    ax.plot(df["data"], df["MM20"], color="blue", label="MM20")
    ax.plot(df["data"], df["MM50"], color="red", label="MM50")
    ax.fill_between(df["data"], df["Banda_superior"], df["Banda_inferior"], color="gray", alpha=0.3, label="Bandas de Bollinger")
    ax.legend()
    ax2 = ax.twinx()
    ax2.set_ylabel("Volume")
    ax2.bar(df["data"], df["volume"], color="green", alpha=0.5, label="Volume")
    ax2.legend(loc="upper left")
    canvas = FigureCanvas(fig)
    return canvas

def update_grafico():
    # Esta função é chamada periodicamente usando um mecanismo de threading ou de eventos, e atualiza o gráfico em tempo real com os dados mais recentes da API.
    global grafico
    symbol = ui.tableWidget.item(ui.tableWidget.currentRow(), 0).text()
    interval = "1min"
    df = get_historico(symbol, interval)
    title = f"{symbol} - {interval}"
    grafico = plot_candlestick(df, title)
    ui.verticalLayout_2.addWidget(grafico) 
    ui.label_5.setText(f"Preço atual: R$ {df[‘fechamento’].iloc[-1]}")

def enviar_ordem(): # Esta função recebe uma instância de Ordem e verifica se ela é válida (se há saldo suficiente para comprar ou se há ações suficientes para vender), envia a ordem para a corretora fictícia (que pode ser simulada com uma lista ou um dicionário), atualiza o saldo e a carteira do usuário e mostra uma mensagem na interface gráfica informando o status da ordem. global ordens symbol = ui.tableWidget.item(ui.tableWidget.currentRow(), 0).text() preco = float(ui.tableWidget.item(ui.tableWidget.currentRow(), 1).text()) volume = int(ui.tableWidget.item(ui.tableWidget.currentRow(), 2).text()) acao = Acao(symbol, preco, volume) quantidade = int(ui.lineEdit.text()) tipo = ui.pushButton.text().lower() ordem = Ordem(acao, quantidade, tipo) ordem.executar() if ordem.status == “fechada”: ui.statusbar.showMessage(f"Ordem de {tipo} de {quantidade} {symbol} executada com sucesso a R$ {ordem.preco}“) ui.listWidget.addItem(f”{symbol} - {quantidade} - {tipo} - R$ {ordem.preco} - {ordem.status}“) ui.label_4.setText(f"Saldo: R$ {saldo}”) else: ui.statusbar.showMessage(f"Ordem de {tipo} de {quantidade} {symbol} inválida")

def cancelar_ordem(): # Esta função recebe uma instância de Ordem e verifica se ela está aberta, cancela a ordem na corretora fictícia, atualiza o saldo e a carteira do usuário e mostra uma mensagem na interface gráfica informando o status da ordem. global ordens index = ui.listWidget.currentRow() if index != -1: ordem = ordens[index] ordem.cancelar() if ordem.status == “cancelada”: ui.statusbar.showMessage(f"Ordem de {ordem.tipo} de {ordem.quantidade} {ordem.acao.nome} cancelada") ui.listWidget.item(index).setText(f"{ordem.acao.nome} - {ordem.quantidade} - {ordem.tipo} - R$ {ordem.preco} - {ordem.status}")

def calcular_resultado(): # Esta função recebe uma instância de Ordem e verifica se ela está fechada, calcula o resultado da operação (lucro ou prejuízo), atualiza o saldo e a carteira do usuário e mostra uma mensagem na interface gráfica informando o resultado. global ordens index = ui.listWidget.currentRow() if index != -1: ordem = ordens[index] resultado = ordem.calcular_resultado() if resultado is not None: if resultado > 0: ui.statusbar.showMessage(f"Lucro de R$ {resultado}“) elif resultado < 0: ui.statusbar.showMessage(f"Prejuízo de R$ {-resultado}”) else: ui.statusbar.showMessage(f"Empate")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("interface.ui", self) # Carrega o arquivo interface.ui
        self.setWindowTitle("Plataforma de Trading") # Define o título da janela
        self.tableWidget.setRowCount(10) # Define o número de linhas da tabela
        self.tableWidget.setColumnCount(3) # Define o número de colunas da tabela
        self.tableWidget.setHorizontalHeaderLabels(["Nome", "Preço", "Volume"]) # Define os nomes das colunas da tabela
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Ajusta o tamanho das colunas da tabela
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection) # Permite selecionar apenas uma linha da tabela por vez
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows) # Permite selecionar a linha inteira da tabela
        self.listWidget.setSelectionMode(QAbstractItemView.SingleSelection) # Permite selecionar apenas um item da lista por vez
        self.listWidget.setHorizontalHeaderLabels(["Ação", "Quantidade", "Tipo", "Preço", "Status"]) # Define os nomes das colunas da lista
        self.listWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Ajusta o tamanho das colunas da lista
        self.label_4.setText(f"Saldo: R$ {saldo}") # Mostra o saldo inicial do usuário
        self.label_5.setText("Preço atual: -") # Mostra o preço atual da ação selecionada na tabela
        self.pushButton.clicked.connect(enviar_ordem) # Conecta o botão "Comprar" com a função enviar_ordem
        self.pushButton_2.clicked.connect(enviar_ordem) # Conecta o botão "Vender" com a função enviar_ordem
        self.pushButton_3.clicked.connect(cancelar_ordem) # Conecta o botão "Cancelar" com a função cancelar_ordem
        self.pushButton_4.clicked.connect(calcular_resultado) # Conecta o botão "Resultado" com a função calcular_resultado
        self.tableWidget.itemSelectionChanged.connect(get_historico) # Conecta a seleção de uma linha da tabela com a função get_historico
        self.timer = QTimer(self) # Cria um temporizador para atualizar o gráfico em tempo real
        self.timer.timeout.connect(update_grafico) # Conecta o temporizador com a função update_grafico
        self.timer.start(60000) # Inicia o temporizador com um intervalo de 60 segundos

app = QApplication(sys.argv) # Cria a instância da aplicação
window = MainWindow() # Cria a instância da interface gráfica
window.show() # Mostra a interface gráfica na tela
app.exec_() # Executa a aplicação