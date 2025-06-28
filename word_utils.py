
import os
from docx import Document
from docx.shared import Cm, Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.enum.text import WD_BREAK
from PIL import Image, UnidentifiedImageError

PASTAS_TEXTO_NORMAL = ["- Detalhes", "- Vista ampla"]

def aplicar_estilo(run, tamanho, negrito=False):
    run.font.name = "Arial"
    run.font.size = Pt(tamanho)
    run.bold = negrito

def inserir_conteudo(modelo_path, conteudo, output_path, campos=None):
    doc = Document(modelo_path)
    contador_imagens = 0
    conteudo_processado = False
    paragrafo_insercao_index = None

    # --- Nova Lógica: Substituir placeholders com dados do formulário ---
    if campos:
        # Substituir em parágrafos
        for p in doc.paragraphs:
            for key, value in campos.items():
                placeholder = f'{{{{{key.lower()}}}}}'
                if placeholder in p.text:
                    # Limpar o parágrafo e recriar com formatação
                    p.clear()
                    run = p.add_run(str(value))
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)
                    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Substituir em tabelas
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for key, value in campos.items():
                            placeholder = f'{{{{{key.lower()}}}}}'
                            if placeholder in p.text:
                                # Limpar o parágrafo e recriar com formatação
                                p.clear()
                                run = p.add_run(str(value))
                                run.font.name = "Calibri"
                                run.font.size = Pt(11)
                                p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        # Substituir em cabeçalhos e rodapés
        for section in doc.sections:
            # Cabeçalho
            for p in section.header.paragraphs:
                for key, value in campos.items():
                    placeholder = f'{{{{{key.lower()}}}}}'
                    if placeholder in p.text:
                        # Limpar o parágrafo e recriar com formatação
                        p.clear()
                        run = p.add_run(str(value))
                        run.font.name = "Calibri"
                        run.font.size = Pt(11)
                        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
            
            # Rodapé
            for p in section.footer.paragraphs:
                for key, value in campos.items():
                    placeholder = f'{{{{{key.lower()}}}}}'
                    if placeholder in p.text:
                        # Limpar o parágrafo e recriar com formatação
                        p.clear()
                        run = p.add_run(str(value))
                        run.font.name = "Calibri"
                        run.font.size = Pt(11)
                        p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    # --- Fim da Nova Lógica ---

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
            if 'image_path' in item:
                image_path = item['image_path']
                if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                    try:
                        # Inserção da imagem (sem legenda)
                        p = doc.paragraphs[paragrafo_insercao_index].insert_paragraph_before('')
                        with Image.open(image_path) as img:
                            largura_original, altura_original = img.size
                            altura_desejada_cm = 10
                            proporcao = altura_desejada_cm / altura_original * 2.54
                            largura_proporcional_cm = largura_original * proporcao / 2.54

                            run = p.add_run()
                            run.add_picture(
                                image_path,
                                width=Cm(largura_proporcional_cm),
                                height=Cm(altura_desejada_cm)
                            )
                            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                            contador_imagens += 1
                            conteudo_processado = True

                    except UnidentifiedImageError:
                        print(f"Erro: Formato de imagem não reconhecido: {image_path}")
                    except Exception as e:
                        print(f"Erro ao inserir imagem '{image_path}': {e}")
                else:
                    print(f"Erro: Arquivo de imagem inválido: {image_path}")

            elif 'quebra_pagina' in item:
                doc.paragraphs[paragrafo_insercao_index].insert_paragraph_before('').add_run().add_break(WD_BREAK.PAGE)
                conteudo_processado = False

    doc.save(output_path)
    return contador_imagens
