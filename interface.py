from tkinter import Tk, filedialog

def selecionar_pasta():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="Selecione a pasta de fotos")

def selecionar_modelo():
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        title="Selecione o modelo do Word",
        filetypes=[("Documentos Word", "*.docx")]
    )

def selecionar_caminho_saida():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title="Selecione a pasta para salvar o relatório")
