from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers

# Ruta al archivo PDF que quieres firmar
pdf_path = "documento.pdf"
# Ruta al archivo .p12
p12_path = "3437941.p12"
# Contraseña del certificado .p12
password = b"Galant1998"
# Nombre del campo de firma (opcional, se puede crear uno si no existe)
signature_field_name = "Firma1"

with open(pdf_path, "rb") as doc:
    w = IncrementalPdfFileWriter(doc)
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file=p12_path, passphrase=password
    )
    out = signers.sign_pdf(
        w,
        signers.PdfSignatureMetadata(field_name=signature_field_name),
        signer=signer,
    )
    with open("documento_firmado.pdf", "wb") as signed_doc:
        signed_doc.write(out.read())

print("Documento PDF firmado exitosamente como documento_firmado.pdf")




