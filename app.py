from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import tempfile
import zipfile
import shutil
from interface import selecionar_pasta, selecionar_modelo
from word_utils import inserir_conteudo
from werkzeug.utils import secure_filename
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
    if 'pasta_fotos' not in request.files:
        flash('Nenhum arquivo enviado.')
        return redirect(url_for('index'))

    uploaded_file = request.files['pasta_fotos']
    modelo_selecionado = request.form.get('modelo')

    if uploaded_file.filename == '':
        flash('Nenhum arquivo selecionado.')
        return redirect(url_for('index'))

    if not modelo_selecionado:
        flash('Nenhum modelo de relatório selecionado.')
        return redirect(url_for('index'))

    # Normalizar o nome do arquivo para evitar problemas com caracteres especiais
    modelo_filename = modelo_selecionado.replace('ã', 'a').replace('ç', 'c').replace('ó', 'o')
    modelo_path = os.path.join(MODELOS_FOLDER, modelo_filename)
    
    # Se não encontrar com normalização, tentar nome original
    if not os.path.exists(modelo_path):
        modelo_path = os.path.join(MODELOS_FOLDER, modelo_selecionado)
    
    if not os.path.exists(modelo_path):
        print(f"Modelo não encontrado: {modelo_path}")
        print(f"Arquivos disponíveis: {os.listdir(MODELOS_FOLDER) if os.path.exists(MODELOS_FOLDER) else 'Pasta não existe'}")
        flash(f'Modelo "{modelo_selecionado}" não encontrado.')
        return redirect(url_for('index'))

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

    temp_dir = None
    try:
        print(f"Iniciando processamento do arquivo: {uploaded_file.filename}")
        print(f"Modelo selecionado: {modelo_selecionado}")
        
        # Criar um diretório temporário para descompactar o ZIP
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, secure_filename(uploaded_file.filename))
        uploaded_file.save(zip_path)

        # Descompactar o arquivo ZIP
        print("Descompactando arquivo ZIP...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        print("Arquivo descompactado com sucesso")

        # Encontrar a pasta raiz dentro do ZIP
        extracted_contents = os.listdir(temp_dir)
        pasta_raiz_processamento = temp_dir

        # Se há apenas uma pasta, usar ela como raiz
        if len(extracted_contents) == 1 and os.path.isdir(os.path.join(temp_dir, extracted_contents[0])):
            pasta_raiz_processamento = os.path.join(temp_dir, extracted_contents[0])

        # --- Lógica de Leitura de Pastas e Títulos (adaptada de auto.py) ---
        conteudo = []
        nome_pasta_raiz_original = os.path.basename(pasta_raiz_processamento.strip(os.sep))

        for root, dirs, files in os.walk(pasta_raiz_processamento):
            # Ordenar subdiretórios apenas no nível da pasta raiz de processamento
            if root == pasta_raiz_processamento:
                dirs.sort(key=lambda x: (ORDEM_PASTAS.index(x) if x in ORDEM_PASTAS else len(ORDEM_PASTAS), x))

            # Calcular o nível da pasta em relação à pasta raiz de processamento
            rel_path = os.path.relpath(root, pasta_raiz_processamento)
            path_parts = []
            if rel_path != '.':  # Evita que o diretório raiz seja dividido em partes vazias
                path_parts = rel_path.split(os.sep)

            nivel = len(path_parts)

            # Adicionar títulos de pastas
            if nivel == 0 and rel_path == '.':  # A própria pasta raiz de processamento
                # Não adicionamos a pasta raiz como título, pois o relatório é sobre ela
                pass
            elif nivel == 1:
                conteudo.append(path_parts[0])
            elif nivel == 2:
                conteudo.append(f"»{path_parts[1]}")
            elif nivel == 3:
                conteudo.append(f"»»{path_parts[2]}")
            else:
                # Para níveis mais profundos
                if path_parts:  # Garante que path_parts não está vazio
                    conteudo.append(f"»»»- {path_parts[-1]}")

            # Adicionar caminhos das imagens
            arquivos_imagens = [
                os.path.join(root, file)
                for file in files
                if file.lower().endswith(('.png', '.jpg', '.jpeg'))
            ]
            arquivos_imagens.sort()  # Garante uma ordem consistente das imagens

            # Adicionar imagens como dicionários para compatibilidade com word_utils.py
            for imagem_path in arquivos_imagens:
                conteudo.append({"image_path": imagem_path})

            # Adicionar quebra de página se houver imagens
            if arquivos_imagens:
                conteudo.append({"quebra_pagina": True})

        # --- Fim da Lógica de Leitura de Pastas e Títulos ---

        # Gerar o nome do arquivo de saída
        nome_projeto = campos['nome'] or nome_pasta_raiz_original
        output_filename = f"RELATÓRIO FOTOGRÁFICO - {nome_projeto} - LEVANTAMENTO PREVENTIVO.docx"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)

        # Inserir conteúdo no modelo
        print(f"Processando {len([item for item in conteudo if isinstance(item, dict) and 'image_path' in item])} imagens...")
        contador_imagens = inserir_conteudo(modelo_path, conteudo, output_path, campos)
        print(f"Processamento concluído. Imagens inseridas: {contador_imagens}")

        flash(f'Relatório gerado com sucesso! {contador_imagens} imagens inseridas.')
        return send_file(output_path, as_attachment=True, download_name=output_filename)

    except zipfile.BadZipFile:
        flash('O arquivo enviado não é um arquivo ZIP válido.')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Erro detalhado: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Ocorreu um erro ao processar o arquivo: {str(e)}')
        return redirect(url_for('index'))
    finally:
        # Limpar o diretório temporário
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)