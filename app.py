import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, render_template, request

load_dotenv()
app = Flask(__name__)

# Configuração da API do Google AI
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Chave de API do Google não encontrada. Verifique seu arquivo .env")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro-latest')
except Exception as e:
    print(f"ERRO CRÍTICO: Não foi possível configurar a API do Gemini. {e}")
    model = None

def get_db_connection():
    conn = sqlite3.connect('portal.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/busca', methods=['GET', 'POST'])
def busca():
    resultado_encontrado = None
    codigo_buscado = ""
    informacao_ia = None

    if request.method == 'POST':
        codigo_buscado = request.form.get('cid_code', '').strip().upper()
    else:
        codigo_buscado = request.args.get('cid_code', '').strip().upper()

    if codigo_buscado:
        conn = get_db_connection()
        resultado_encontrado = conn.execute('SELECT * FROM cids WHERE codigo = ?', (codigo_buscado,)).fetchone()
        
        if resultado_encontrado:
            cached_response = conn.execute('SELECT resposta_ia FROM cache WHERE cid_codigo = ?', (codigo_buscado,)).fetchone()
            
            if cached_response:
                print(f"Resposta para {codigo_buscado} encontrada no CACHE.")
                informacao_ia = cached_response['resposta_ia']
            elif model: # Só tenta chamar a IA se o modelo foi configurado com sucesso
                print(f"Resposta para {codigo_buscado} não encontrada no cache. Chamando a API...")
                try:
                    prompt = f"""
                    Atue como um especialista em desenvolvimento infantil e saúde mental, explicando o CID abaixo para pais e cuidadores.
                    Instrução Principal: Vá direto para a resposta, começando diretamente com a seção "Explicação Simplificada". Não inclua nenhuma frase de introdução, preâmbulo ou saudação. Não use formatação markdown.
                    Dados do CID:
                    - Código: {resultado_encontrado['codigo']}
                    - Nome: {resultado_encontrado['nome']}
                    - Descrição Oficial: {resultado_encontrado['descricao']}
                    Seções Requeridas:
                    1. Explicação Simplificada: O que este código significa em termos práticos para o dia a dia da criança?
                    2. Principais Sinais e Características: Quais são os comportamentos ou desafios mais comuns que os pais podem observar?
                    3. Primeiros Passos e Sugestões: O que os pais podem fazer após receber este diagnóstico?
                    """
                    
                    response = model.generate_content(prompt)
                    informacao_ia = response.text

                    conn.execute('INSERT INTO cache (cid_codigo, resposta_ia) VALUES (?, ?)', (codigo_buscado, informacao_ia))
                    conn.commit()
                    print(f"Resposta para {codigo_buscado} salva no cache.")

                except Exception as e:
                    print(f"Erro ao chamar a API do Gemini: {e}")
                    informacao_ia = "Não foi possível carregar informações adicionais da IA neste momento."
            else:
                informacao_ia = "A integração com a IA não está configurada corretamente."
        
        conn.close()
                
    return render_template('busca.html', resultado=resultado_encontrado, busca=codigo_buscado, informacao_ia=informacao_ia)

@app.route('/identificacao', methods=['GET', 'POST'])
def identificacao():
    if request.method == 'POST':
        caracteristicas_selecionadas = request.form.getlist('caracteristicas')
        
        if not caracteristicas_selecionadas:
            return render_template('identificacao.html', resultados=None)

        conn = get_db_connection()
        todos_os_cids = conn.execute("SELECT * FROM cids WHERE tags IS NOT NULL AND tags != ''").fetchall()
        conn.close()

        resultados = []
        for cid in todos_os_cids:
            tags_do_cid = cid['tags'].split(',')
            pontuacao = 0
            for tag in tags_do_cid:
                if tag.strip() in caracteristicas_selecionadas:
                    pontuacao += 1
            
            if pontuacao > 0:
                resultados.append({'cid': cid, 'pontuacao': pontuacao})
        
        resultados_ordenados = sorted(resultados, key=lambda x: x['pontuacao'], reverse=True)
        
        return render_template('identificacao.html', resultados=resultados_ordenados)

    return render_template('identificacao.html', resultados=None)

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        nome = request.form.get('name')
        email = request.form.get('email')
        mensagem = request.form.get('message')
        print(f"Mensagem Recebida de {nome} ({email}): {mensagem}")
        return render_template('sucesso.html')
    
    return render_template('contato.html')

if __name__ == '__main__':
    from waitress import serve
    print("Servidor de produção iniciado em http://127.0.0.1:5000")
    serve(app, host='0.0.0.0', port=5000)
