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
        self.nome = nome
        self.preco = preco
        self.volume = volume

class Ordem:
    def __init__(self, acao, quantidade, tipo):
        self.acao = acao
        self.quantidade = quantidade
        self.tipo = tipo
        self.status = "aberta"
        self.preco = None

    def validar(self):
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
        if self.status == "aberta":
            self.status = "cancelada"

    def calcular_resultado(self):
        if self.status == "fechada":
            if self.tipo == "compra":
                return (self.acao.preco - self.preco) * self.quantidade
            elif self.tipo == "venda":
                return (self.preco - self.acao.preco) * self.quantidade

saldo = 10000 
carteira = {} 
grafico = None 
ordens = [] 

def calcular_indicadores(df):
    df["MM20"] = df["fechamento"].rolling(20).mean()
    df["MM50"] = df["fechamento"].rolling(50).mean()
    df["Banda_superior"] = df["MM20"] + 2 * df["fechamento"].rolling(20).std()
    df["Banda_inferior"] = df["MM20"] - 2 * df["fechamento"].rolling(20).std()
    df["EMA12"] = df["fechamento"].ewm(span=12).mean()
    df["EMA26"] = df["fechamento"].ewm(span=26).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Sinal"] = df["MACD"].ewm(span=9).mean()
    df["Histograma"] = df["MACD"] - df["Sinal"]
    return df

def get_historico(symbol, interval):
    url = f"https://api.bing.com/finance/historical?symbol={symbol}&interval={interval}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data)
    df.columns = ["data", "abertura", "maxima", "minima", "fechamento", "volume"]
    return df

def plot_candlestick(df, title):
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
    global grafico
    symbol = ui.tableWidget.item(ui.tableWidget.currentRow(), 0).text()
    interval = "1min"
    df = get_historico(symbol, interval)
    title = f"{symbol} - {interval}"
    grafico = plot_candlestick(df, title)
    ui.verticalLayout_2.addWidget(grafico)
    ui.label_5.setText(f"Preço atual: R$ {df['fechamento'].iloc[-1]}")

def enviar_ordem():
    global ordens
    symbol = ui.tableWidget.item(ui.tableWidget.currentRow(), 0).text()
    preco = float(ui.tableWidget.item(ui.tableWidget.currentRow(), 1).text())
    volume = int(ui.tableWidget.item(ui.tableWidget.currentRow(), 2).text())
    acao = Acao(symbol, preco, volume)
    quantidade = int(ui.lineEdit.text())
    tipo = ui.pushButton.text().lower()
    ordem = Ordem(acao, quantidade, tipo)
    ordem.executar()
    if ordem.status == "fechada":
        ui.statusbar.showMessage(f"Ordem de {tipo} de {quantidade} {symbol} executada com sucesso a R$ {ordem.preco}")
        ui.listWidget.addItem(f"{symbol} - {quantidade} - {tipo} - R$ {ordem.preco} - {ordem.status}")
        ui.label_4.setText(f"Saldo: R$ {saldo}")
        ordens.append(ordem)
    else:
        ui.statusbar.showMessage(f"Ordem de {tipo} de {quantidade} {symbol} inválida")

def cancelar_ordem():
    global ordens
    index = ui.listWidget.currentRow()
    if index != -1 and index < len(ordens):
        ordem = ordens[index]
        ordem.cancelar()
        if ordem.status == "cancelada":
            ui.statusbar.showMessage(f"Ordem de {ordem.tipo} de {ordem.quantidade} {ordem.acao.nome} cancelada")
            ui.listWidget.item(index).setText(f"{ordem.acao.nome} - {ordem.quantidade} - {ordem.tipo} - R$ {ordem.preco} - {ordem.status}")

def calcular_resultado():
    global ordens
    index = ui.listWidget.currentRow()
    if index != -1 and index < len(ordens):
        ordem = ordens[index]
        resultado = ordem.calcular_resultado()
        if resultado is not None:
            if resultado > 0:
                ui.statusbar.showMessage(f"Lucro de R$ {resultado}")
            elif resultado < 0:
                ui.statusbar.showMessage(f"Prejuízo de R$ {-resultado}")
            else:
                ui.statusbar.showMessage(f"Empate")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("interface.ui", self)
        self.setWindowTitle("Plataforma de Trading")
        self.tableWidget.setRowCount(10)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Nome", "Preço", "Volume"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.listWidget.setHorizontalHeaderLabels(["Ação", "Quantidade", "Tipo", "Preço", "Status"])
        self.listWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.label_4.setText(f"Saldo: R$ {saldo}")
        self.label_5.setText("Preço atual: -")
        self.pushButton.clicked.connect(enviar_ordem)
        self.pushButton_2.clicked.connect(enviar_ordem)
        self.pushButton_3.clicked.connect(cancelar_ordem)
        self.pushButton_4.clicked.connect(calcular_resultado)
        self.tableWidget.itemSelectionChanged.connect(get_historico)
        self.timer = QTimer(self)
        self.timer.timeout.connect(update_grafico)
        self.timer.start(60000)

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
