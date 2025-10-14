import sqlite3
import csv

DB_NAME = 'portal.db'

tags_map = {
    "F84.0": "nao_responde_nome,repete_frases,nao_faz_contato_visual,prefere_brincar_sozinho,movimentos_repetitivos,interesses_restritos,sensibilidade_sensorial",
    "F84.5": "linguagem_inapropriada,interesses_restritos,dificuldade_aprendizado,nao_faz_contato_visual",
    "F90.0": "dificuldade_aprendizado,hiperatividade_impulsividade,desatencao,crises_birra_intensas",
    "F80.1": "dificuldade_fala,linguagem_inapropriada,dificuldade_aprendizado",
    "F80.2": "dificuldade_fala,nao_responde_nome,dificuldade_aprendizado",
    "F81.0": "dificuldade_aprendizado,desatencao",
    "F81.2": "dificuldade_aprendizado,desatencao",
    "F70": "dificuldade_aprendizado,dificuldade_fala",
    "F95.2": "movimentos_repetitivos,hiperatividade_impulsividade",
    "F93.0": "crises_birra_intensas,prefere_brincar_sozinho",
    "F98.5": "dificuldade_fala"
}

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
print(f"Banco de dados '{DB_NAME}' conectado.")

cursor.execute("DROP TABLE IF EXISTS cids")
cursor.execute("DROP TABLE IF EXISTS cache")
print("Tabelas antigas removidas.")

cursor.execute("""
CREATE TABLE cids (
    codigo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    capitulo TEXT,
    tags TEXT
)
""")
print("Nova tabela 'cids' criada.")

cursor.execute("""
CREATE TABLE cache (
    cid_codigo TEXT PRIMARY KEY,
    resposta_ia TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
print("Nova tabela 'cache' criada.")

with open('cid10_data.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader)
    count = 0
    for row in reader:
        codigo, nome, descricao = row
        tags = tags_map.get(codigo, "")
        cursor.execute(
            "INSERT INTO cids (codigo, nome, descricao, capitulo, tags) VALUES (?, ?, ?, ?, ?)",
            (codigo, nome, descricao, "Capítulo V (F)", tags)
        )
        count += 1

print(f"{count} registros inseridos na tabela 'cids'.")

conn.commit()
print("Alterações salvas.")
conn.close()
print("Conexão fechada. Processo concluído!")