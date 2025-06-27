
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import tempfile
from interface import selecionar_pasta, selecionar_modelo
from word_utils import inserir_conteudo
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

ORDEM_PASTAS = ["- Área externa", "- Área interna", "- Segundo piso"]
UPLOAD_FOLDER = 'uploads'
MODELOS_FOLDER = '01 - MODELOS'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    # Listar modelos disponíveis
    modelos = []
    if os.path.exists(MODELOS_FOLDER):
        modelos = [f for f in os.listdir(MODELOS_FOLDER) if f.endswith('.docx')]
    return render_template('index.html', modelos=modelos)

@app.route('/upload_fotos', methods=['POST'])
def upload_fotos():
    # Verificar se uma pasta foi enviada
    if 'pasta_fotos' not in request.files:
        flash('Nenhuma pasta selecionada')
        return redirect(url_for('index'))
    
    files = request.files.getlist('pasta_fotos')
    modelo_selecionado = request.form.get('modelo')
    nome_projeto = request.form.get('nome_projeto', 'Projeto')
    
    if not modelo_selecionado:
        flash('Selecione um modelo')
        return redirect(url_for('index'))
    
    # Criar diretório temporário mantendo a estrutura original
    pasta_fotos = os.path.join(UPLOAD_FOLDER, secure_filename(nome_projeto))
    os.makedirs(pasta_fotos, exist_ok=True)
    
    # Salvar arquivos mantendo a estrutura de pastas
    for file in files:
        if file.filename != '':
            # Usar o webkitRelativePath para manter a estrutura de pastas
            relative_path = getattr(file, 'filename', '')
            if hasattr(file, 'webkitRelativePath'):
                relative_path = file.webkitRelativePath
            
            # Criar o caminho completo mantendo a estrutura
            file_path = os.path.join(pasta_fotos, secure_filename(relative_path))
            dir_path = os.path.dirname(file_path)
            
            os.makedirs(dir_path, exist_ok=True)
            file.save(file_path)
    
    # Gerar relatório
    modelo_path = os.path.join(MODELOS_FOLDER, modelo_selecionado)
    nome_arquivo_saida = f"RELATÓRIO FOTOGRÁFICO - {nome_projeto} - LEVANTAMENTO PREVENTIVO.docx"
    arquivo_saida = os.path.join(UPLOAD_FOLDER, nome_arquivo_saida)
    
    # Processar estrutura de pastas e imagens
    conteudo = processar_estrutura_pastas(pasta_fotos)
    
    try:
        contador_imagens = inserir_conteudo(modelo_path, conteudo, arquivo_saida)
        flash(f'Relatório gerado com sucesso! {contador_imagens} imagens inseridas.')
        return send_file(arquivo_saida, as_attachment=True, download_name=nome_arquivo_saida)
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}')
        return redirect(url_for('index'))

def processar_estrutura_pastas(pasta_raiz):
    conteudo = []
    
    for root, dirs, files in os.walk(pasta_raiz):
        if root == pasta_raiz:
            dirs.sort(key=lambda x: (ORDEM_PASTAS.index(x) if x in ORDEM_PASTAS else len(ORDEM_PASTAS), x))
        
        path_parts = os.path.relpath(root, pasta_raiz).split(os.sep)
        nivel = len(path_parts)
        
        if nivel == 1 and path_parts[0] != '.':
            conteudo.append(path_parts[0])
        elif nivel == 2:
            conteudo.append(f"»{path_parts[1]}")
        elif nivel == 3:
            conteudo.append(f"»»{path_parts[2]}")
        elif nivel > 3:
            conteudo.append(f"»»»- {path_parts[-1]}")
        
        arquivos_imagens = [
            os.path.join(root, file)
            for file in files
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        arquivos_imagens.sort(key=os.path.getctime)
        
        for imagem_path in arquivos_imagens:
            conteudo.append({"imagem": imagem_path})
        
        if arquivos_imagens:  # Só adiciona quebra de página se houver imagens
            conteudo.append({"quebra_pagina": True})
    
    return conteudo

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
