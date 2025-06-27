import os
from interface import selecionar_pasta, selecionar_modelo, selecionar_caminho_saida
from word_utils import inserir_conteudo
import tkinter as tk
from tkinter import messagebox

ORDEM_PASTAS = ["- Área externa", "- Área interna", "- Segundo piso"]

def criar_relatorio():
    pasta_raiz = selecionar_pasta()
    if not pasta_raiz:
        print("Nenhuma pasta selecionada. Encerrando.")
        return

    modelo_path = selecionar_modelo()
    if not modelo_path:
        print("Nenhum modelo selecionado. Encerrando.")
        return

    caminho_saida = selecionar_caminho_saida()
    if not caminho_saida:
        print("Nenhum caminho de saída selecionado. Encerrando.")
        return

    nome_pasta_raiz = os.path.basename(pasta_raiz.strip(os.sep))
    os.makedirs(caminho_saida, exist_ok=True)
    nome_arquivo_saida = os.path.join(caminho_saida, f"RELATÓRIO FOTOGRÁFICO - {nome_pasta_raiz} - LEVANTAMENTO PREVENTIVO.docx")

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

    contador_imagens = inserir_conteudo(modelo_path, conteudo, nome_arquivo_saida)
    print(f"Documento '{nome_arquivo_saida}' criado com sucesso!")
    print(f"Número total de imagens inseridas: {contador_imagens}")

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Sucesso", f"Relatório gerado com sucesso!\n\n{contador_imagens} imagens inseridas.")

if __name__ == "__main__":
    criar_relatorio()
