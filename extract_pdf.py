import pdfplumber

pdf_path = r'c:\Users\HP\Desktop\Projet_evaporation_cristallisation_PIC11\evapo_crista_pic-1.pdf'

with pdfplumber.open(pdf_path) as pdf:
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text() + "\n\n"
    
print(full_text)
