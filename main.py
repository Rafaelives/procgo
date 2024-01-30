from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from firebase_admin import credentials, firestore, initialize_app, storage
from flask_babel import Babel
import os
import logging
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import base64
from dash import Dash, dcc, Input, Output
import plotly.express as px
import dash_html_components as dash_html
import base64
from google.cloud import storage
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dash import Dash, dcc, Input, Output, html
import datetime
from google.cloud import storage

bucket_name = 'gs://cgo-analises'
blob_name = 'ALALISE KIL2222.xlsx'


now = datetime.datetime.now()
print("Data e hora atual:", now)

# Adicionar 5 dias à data atual
future_date = now + datetime.timedelta(days=5)
print("Data em 5 dias:", future_date)

# Formatar a data em uma string
formatted_date = now.strftime("%Y-%m-%d %H:%M:%S")
print("Data formatada:", formatted_date)

# Converter uma string para datetime
date_string = "2023-01-01 12:00:00"
converted_date = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

print("Data convertida:", converted_date)
client = storage.Client()

server = Flask(__name__)
server.secret_key = 'sua_chave_secreta_estatica'
babel = Babel(server)
server.config['BABEL_DEFAULT_LOCALE'] = 'pt'

cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
initialize_app(cred, {'storageBucket': 'gs://cgo-analises'})

buckets = client.list_buckets()
for bucket in buckets:
    print(bucket.name)
    
firestore_db = firestore.client()
logging.basicConfig(level=logging.DEBUG)
server.logger.setLevel(logging.DEBUG)

# Criando o aplicativo Dash, usando o servidor Flask
dash_app = Dash(__name__, server=server, url_base_pathname='/dashboard/')
dash_app.layout = dash_html.Div([
    # Seu layout do Dash vai aqui
    dash_html.H1("Dashboard")
    # Mais componentes Dash...
])

#df_excel = pd.read_excel(BytesIO(460.002 bytes))


@server.route('/')
def index():
    return render_template('home.html')

@server.route('/home')
def home():
    return render_template('home.html')

@server.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@server.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@server.errorhandler(500)
def handle_500_error(e):
    response = {'error': 'Internal Server Error'}
    return jsonify(response), 500

@server.route('/alguma-rota')
def alguma_funcao():
    try:
    # Algum código que pode levantar uma exceção
        resultado = 10 / 0
    except ZeroDivisionError as e:
        # Este bloco será executado se uma ZeroDivisionError ocorrer
        print("Erro de divisão por zero:", e)
import logging
from logging.handlers import RotatingFileHandler

@server.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = ''
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        usuario = firestore_db().find_one({'email': email})  # Substitua 'seua_colecao_login' pelo nome da sua coleção de login
        if usuario and check_password_hash(usuario.get('senha'), senha):
            session['usuario_logado'] = usuario.get('email')
            return redirect(url_for('home'))
        else:
            mensagem = 'Email ou senha incorretos.'
    return render_template('cadastro.html', mensagem=mensagem)


@server.route('/esqueceu_senha', methods=['GET', 'POST'])
def forgot_password():
    
    return render_template('esqueceu_senha.html')


@server.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = generate_password_hash(request.form['senha'])

        adicionar_usuario(nome, email, senha)

        return redirect(url_for('login')) 
    return render_template('cadastro.html')

@server.route('/agenda')
def agenda():
    return render_template('agenda.html')

@server.route('/relatorio', methods=['GET', 'POST'])
def relatorio():
    dados=[]
    if request.method == 'POST':
        # Coletar dados do formulário
        data = request.form['data']
        turno = request.form['turno']
        modalidade = request.form['modalidade']
        viatura = request.form['viatura']
        # ... continuar para os outros campos ...

        # Salvar os dados coletados
        dados.append({
            'data': data,
            'turno': turno,
            'modalidade': modalidade,
            'viatura': viatura,
            # ... continuar para os outros campos ...
        })

        return redirect(url_for('graficos'))
    return render_template('relatorio.html')

@server.route('/dashboard')
def render_dashboard():
    return dash_app.index()


@server.route('/efetivo', methods=['GET', 'POST'])
def efetivo():
    print("Entrando na rota /efetivo")
    resultados = []

    if request.method == 'POST':
        matricula = request.form.get('MATRÍCULA')
        pos_gra = request.form.get('POS/GRA')
        nome = request.form.get('NOME')

        try:
            # Ordenar os resultados pelo nome em ordem ascendente
            query = firestore_db.collection("EFETIVOPMCE").order_by("NOME")

            # Se o nome é fornecido, busque todos os documentos e filtre no lado do servidor
            if nome:
                nome = nome.lower()
                todos_resultados = query.stream()
                resultados = [doc.to_dict() for doc in todos_resultados if nome in doc.to_dict().get('NOME', '').lower()]
            else:
                # Aplicar filtros para matrícula e pos_gra se fornecidos
                if matricula:
                    query = query.where('MATRÍCULA', '==', matricula)
                if pos_gra:
                    query = query.where('POS/GRA', '==', pos_gra)

                # Execute a consulta com os filtros adicionados
                resultados = [doc.to_dict() for doc in query.stream()]

            print("Resultados encontrados:", resultados)
        except Exception as e:
            print("Erro ao realizar consulta:", e)

        return render_template('efetivo.html', resultados=resultados)

    # Se não for uma requisição POST, simplesmente renderize o template sem resultados
    return render_template('efetivo.html', resultados=[])


@server.route('/gestao', methods=['GET', 'POST'])
def gestao():
    print("Entrando na rota /gestao")
    resultados = []

    evento_ref = firestore_db.collection("EVENTO")
    query = evento_ref.where("evento", "array_contains", "EVENTO")

    if request.method == 'POST':
        # Obtenha 'tipo_de_evento' do formulário
        tipo_de_evento = request.form.get('TIPO DE EVENTO')  # Certifique-se de que o nome do campo está correto
        termo_busca = request.form.get('termo_busca')  # Supondo que 'termo_busca' também vem do formulário

        if tipo_de_evento:
            query = firestore_db.collection("OPERAÇÕES").where('TIPO DE EVENTO', '==', tipo_de_evento)
           
    
        try:
            query = firestore_db.collection('OPERAÇÕES')
            # Obtém os dados do formulário
            data_inicial = request.form.get('dataInicial')
            data_final = request.form.get('dataFinal')
            evento = request.form.get('evento')
            tipo_de_evento = request.form.get('tipoDeEvento')
            prazo = request.form.get('prazo')
           
            if evento:  
                query = firestore_db.collection("OPERAÇÕES").where('EVENTO', '==', evento)
                firestore_db.collection("OPERAÇÕES").where('EVENTO', 'array_contains', termo_busca)
            if prazo:
                query = firestore_db.collection("OPERAÇÕES").where("PRAZO", '==', prazo)
                firestore_db.collection("OPERAÇÕES").where('PRAZO', 'array_contains', termo_busca) 
            if data_inicial:
                query = firestore_db.collection("OPERAÇÕES").where('DATA INICIAL', '==', data_inicial)
                firestore_db.collection("OPERAÇÕES").where('DATA FINAL', 'array_contains', termo_busca) 
                formato_data = '%Y-%m-%d'     
            if  data_final:
                data_final_formatada = datetime.strptime(data_inicial, formato_data)
                query = query.where('DATA FINAL', '<=', data_final_formatada)
                
            resultados = [doc.to_dict() for doc in query.stream()]

            print(print(os.getcwd("Resultados encontrados:", resultados)))

            # Retorna os resultados em JSON
            return jsonify(resultados)
        except Exception as e:
            return jsonify({"erro": str(e)})


@server.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    return redirect(url_for('login'))

@server.route('/plot', methods=['POST'])
def plot():
    # Substitua 'sua_coluna' pelo nome real da coluna de dados
    coluna_dados = 'QUANTIDADE DE ARMAS DE FOGO APREENDIDAS'
    bucket = storage.bucket()
    blob = bucket.blob('ALALISE KIL2222.xlsx')
    blob.read_excel('gs://cgo-analises')
    df = pd.read_excel('gs://cgo-analises')
    # Somar os valores da coluna de dados
    soma_valores = df[coluna_dados].sum()

    local_path = 'ALALISE_KIL2222.xlsx'
    bucket = storage.bucket()
    blob = bucket.blob('ALALISE_KIL2222.xlsx')
    blob.download_to_filename(local_path)
    df = pd.read_excel(local_path)

    # Somar os valores da coluna de dados
    soma_valores = df[coluna_dados].sum()

    # Criar um gráfico de barras com a soma dos valores
    fig, ax = plt.subplots()
    ax.bar(['Total'], [soma_valores])
    ax.set_ylabel('Quantidade')
    ax.set_title('Total de ' + coluna_dados)

    # Converter o gráfico em uma imagem PNG em base64
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')

    # Fechar a figura para não consumir memória
    plt.close(fig)
        # Retornar a imagem codificada para o frontend
    return render_template('plot.html', plot_url=plot_url)


def read_data_from_storage(blob_name):
    df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')
    df_excel = pd.read_excel('//cgo-analises/ALALISE KIL2222.xlsx')
    """ Função para ler dados do Firebase Storage e retornar um DataFrame """
    client = storage.Client()
    bucket = client.bucket(df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv'))
    blob = bucket.blob(blob_name)
    data_stream = BytesIO()
    blob.download_to_file(data_stream)
    data_stream.seek(0)
    if blob_name.endswith('.csv'):
        return pd.read_csv(data_stream)
    elif blob_name.endswith('.xlsx'):
        return pd.read_excel(data_stream)
    else:
        raise ValueError("Formato de arquivo não suportado")

def create_plot(df, title, xlabel, ylabel):
    """ Função para criar um gráfico e retornar a URL da imagem codificada em base64 """
    plt.figure(figsize=(10,5))
    df.plot(kind='bar')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.read()).decode('utf-8')
    return plot_url


def adicionar_usuario(nome, email, senha):
    try:
        # Use firestore_db para referenciar a coleção
        usuarios_ref = firestore_db.collection('login')
        usuarios_ref.add({
            'nome': nome,
            'email': email,
            'senha': senha
        })
        return True
    except Exception as e:
        logging.error(f"Erro ao adicionar usuário: {e}")
        return False


def obter_url_publica_arquivo():
    storage_client = storage.Client()
    bucket = storage_client.bucket('ggo-planejamentos.appspot.com')
    blob = bucket.blob('OPERACOES.xlsx')
    blob.make_public()
    return blob.public_url

# Função para ler dados do Storage e retornar um DataFrame
def read_data_from_storage(filename):
    bucket = storage.bucket()
    blob = bucket.blob(filename)
    blob.download_to_filename(filename)

    if filename.endswith('.csv'):
        df = pd.read_csv(filename)
    elif filename.endswith('.xlsx'):
        df = pd.read_excel(filename)
    else:
        raise ValueError("Formato de arquivo não suportado")

    return df

def plot_data(df):
    # Exemplo: Plotar um gráfico de barras
    # Supondo que 'df' tenha uma coluna 'Category' e outra 'Values'
    if 'Category' in df.columns and 'Values' in df.columns:
        df.groupby('Category')['Values'].sum().plot(kind='bar')
        plt.xlabel('Categoria')
        plt.ylabel('Valores')
        plt.title('Distribuição de Valores por Categoria')
        plt.show()
    else:
        print("As colunas necessárias não estão presentes no DataFrame")
        
def read_data_from_storage(blob_name):
    bucket = storage.bucket()
    blob = bucket.blob(blob_name)

    data_stream = BytesIO.BytesIO()
    blob.download_to_file(data_stream)
    data_stream.seek(0)

    if blob_name.endswith('.csv'):
        return pd.read_csv(data_stream)
    elif blob_name.endswith('.xlsx'):
        return pd.read_excel(data_stream)
    else:
        raise ValueError("Formato de arquivo não suportado")


def create_plot(df):
    # Suponha que você quer somar valores na coluna 'Valores' e agrupá-los por 'Categoria'
    grouped_data = df.groupby('Categoria')['Valores'].sum()
    grouped_data.plot(kind='bar')
    plt.xlabel('Categoria')
    plt.ylabel('Soma dos Valores')
    plt.title('Soma dos Valores por Categoria')
    plt.show()

# Main
def main():
    file_name = 'your_file.csv'  # Altere para o nome do seu arquivo
    df = read_data_from_storage(file_name)
    create_plot(df)

    
def salvar_url_no_firestore(url):
    doc_ref = firestore_db.collection('OPERAÇÕES').document('documento_operacoes')
    doc_ref.set({'url_do_arquivo': url})

def buscar_usuario_por_email(email):
    usuarios_ref = firestore_db.collection('login')
    query = usuarios_ref.where('email', '==', email).stream()
    for usuario in query:
        return usuario.to_dict()
    return None

with server.test_request_context():
   
    print(url_for('login'))
    print(url_for('home'))
    print(url_for('cadastro'))
    print(url_for('gestao'))
    
    
if __name__ == '__main__':
    server.run(debug=True)