
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import tempfile
from interface import selecionar_pasta, selecionar_modelo
from word_utils import inserir_conteudo
from werkzeug.utils import secure_filename
import zipfile
from docx import Document

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

ORDEM_PASTAS = ["- Área externa", "- Área interna", "- Segundo piso"]
UPLOAD_FOLDER = 'uploads'
MODELOS_FOLDER = '01 - MODELOS - auto'

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
    
    # Capturar todos os campos do formulário
    campos = {
        'nome': request.form.get('nome', ''),
        'ctr': request.form.get('ctr', ''),
        'os': request.form.get('os', ''),
        'elb': 'Ygor Augusto Fernandes',  # Valor fixo
        'data_elb': request.form.get('data_elb', ''),
        'ag': request.form.get('ag', ''),
        'nome_dependencia': request.form.get('nome_dependencia', ''),
        'uf': request.form.get('uf', ''),
        'tipo': request.form.get('tipo', ''),
        'data_att': request.form.get('data_att', ''),
        'end': request.form.get('end', ''),
        'resp_dep': request.form.get('resp_dep', ''),
        'resp_tec': request.form.get('resp_tec', ''),
        'empresa': 'Ygor Augusto Fernandes'  # Valor fixo
    }
    
    nome_projeto = campos['nome'] or 'Projeto'
    
    if not modelo_selecionado:
        flash('Selecione um modelo')
        return redirect(url_for('index'))
    
    # Criar diretório temporário mantendo a estrutura original
    pasta_fotos = os.path.join(UPLOAD_FOLDER, secure_filename(nome_projeto))
    os.makedirs(pasta_fotos, exist_ok=True)
    
    # Salvar arquivos mantendo a estrutura de pastas
    for file in files:
        if file.filename != '':
            # Extrair o caminho relativo da pasta selecionada
            filename = file.filename
            # No Flask, o webkitRelativePath vem no filename quando webkitdirectory é usado
            relative_path = filename
            
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
        
        # Substituir placeholders no documento gerado
        substituir_placeholders(arquivo_saida, campos)
        
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

        if nivel == 1:
            conteudo.append(path_parts[0])
        elif nivel == 2:
            conteudo.append(f"»{path_parts[1]}")
        elif nivel == 3:
            conteudo.append(f"»»{path_parts[2]}")
        else:
            conteudo.append(f"»»»- {path_parts[-1]}")

        arquivos_imagens = [
            os.path.join(root, file)
            for file in files
            if file.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        arquivos_imagens.sort(key=os.path.getctime)

        for imagem_path in arquivos_imagens:
            conteudo.append({"imagem": imagem_path})

        conteudo.append({"quebra_pagina": True})

    return conteudo

def substituir_placeholders(documento_path, campos):
    """Substitui os placeholders no documento Word pelos valores dos campos"""
    doc = Document(documento_path)
    
    # Dicionário de mapeamento dos placeholders
    placeholders = {
        '{{nome}}': campos.get('nome', ''),
        '{{ctr}}': campos.get('ctr', ''),
        '{{os}}': campos.get('os', ''),
        '{{elb}}': campos.get('elb', ''),
        '{{data_elb}}': campos.get('data_elb', ''),
        '{{ag}}': campos.get('ag', ''),
        '{{nome_dependencia}}': campos.get('nome_dependencia', ''),
        '{{uf}}': campos.get('uf', ''),
        '{{tipo}}': campos.get('tipo', ''),
        '{{data_att}}': campos.get('data_att', ''),
        '{{end}}': campos.get('end', ''),
        '{{resp_dep}}': campos.get('resp_dep', ''),
        '{{resp_tec}}': campos.get('resp_tec', ''),
        '{{empresa}}': campos.get('empresa', '')
    }
    
    # Substituir placeholders em parágrafos
    for paragrafo in doc.paragraphs:
        for placeholder, valor in placeholders.items():
            if placeholder in paragrafo.text:
                paragrafo.text = paragrafo.text.replace(placeholder, valor)
    
    # Substituir placeholders em tabelas
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for placeholder, valor in placeholders.items():
                    if placeholder in celula.text:
                        celula.text = celula.text.replace(placeholder, valor)
    
    # Substituir placeholders em cabeçalhos e rodapés
    for secao in doc.sections:
        # Cabeçalho
        for paragrafo in secao.header.paragraphs:
            for placeholder, valor in placeholders.items():
                if placeholder in paragrafo.text:
                    paragrafo.text = paragrafo.text.replace(placeholder, valor)
        
        # Rodapé
        for paragrafo in secao.footer.paragraphs:
            for placeholder, valor in placeholders.items():
                if placeholder in paragrafo.text:
                    paragrafo.text = paragrafo.text.replace(placeholder, valor)
    
    doc.save(documento_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
