import os
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_BREAK
from PIL import Image, UnidentifiedImageError

PASTAS_TEXTO_NORMAL = ["- Detalhes", "- Vista ampla"]

def aplicar_estilo(run, tamanho, negrito=False):
    run.font.name = "Arial"
    run.font.size = Pt(tamanho)
    run.bold = negrito

def inserir_conteudo(modelo_path, conteudo, output_path):
    doc = Document(modelo_path)
    contador_imagens = 0
    conteudo_processado = False
    paragrafo_insercao_index = None

    for i, paragrafo in enumerate(doc.paragraphs):
        if "{{start_here}}" in paragrafo.text:
            paragrafo_insercao_index = i
            break

    if paragrafo_insercao_index is None:
        print("Marca '{{start_here}}' não encontrada no modelo.")
        return contador_imagens

    conteudo_invertido = list(reversed(conteudo))

    for item in conteudo_invertido:
        if isinstance(item, str):
            titulo = item.replace("»", "").strip() + ":"
            nivel = item.count("»")

            p = doc.paragraphs[paragrafo_insercao_index].insert_paragraph_before('')
            run = p.add_run(titulo)

            if any(pasta in titulo for pasta in PASTAS_TEXTO_NORMAL):
                aplicar_estilo(run, 11, negrito=True)
                p.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
            elif nivel == 0:
                p.style = 'Heading 1'
            elif nivel == 1:
                p.style = 'Heading 2'
            elif nivel == 2:
                p.style = 'Heading 3'
            else:
                aplicar_estilo(run, 12, negrito=True)

            conteudo_processado = True

        elif isinstance(item, dict):
            if 'imagem' in item:
                imagem_path = item["imagem"]
                if os.path.exists(imagem_path) and os.path.getsize(imagem_path) > 0:
                    try:
                        # Inserção da imagem (sem legenda)
                        p = doc.paragraphs[paragrafo_insercao_index].insert_paragraph_before('')
                        with Image.open(imagem_path) as img:
                            largura_original, altura_original = img.size
                            altura_desejada_cm = 10
                            proporcao = altura_desejada_cm / altura_original * 2.54
                            largura_proporcional_cm = largura_original * proporcao / 2.54

                            run = p.add_run()
                            run.add_picture(
                                imagem_path,
                                width=Cm(largura_proporcional_cm),
                                height=Cm(altura_desejada_cm)
                            )
                            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                            contador_imagens += 1
                            conteudo_processado = True

                    except UnidentifiedImageError:
                        print(f"Erro: Formato de imagem não reconhecido: {imagem_path}")
                    except Exception as e:
                        print(f"Erro ao inserir imagem '{imagem_path}': {e}")
                else:
                    print(f"Erro: Arquivo de imagem inválido: {imagem_path}")

            elif 'quebra_pagina' in item:
                doc.paragraphs[paragrafo_insercao_index].insert_paragraph_before('').add_run().add_break(WD_BREAK.PAGE)
                conteudo_processado = False

    doc.save(output_path)
    return contador_imagens
