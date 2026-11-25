"""Génération du contrat de location en PDF avec ReportLab."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER


def generer_contrat_pdf(reservation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
                             topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=16, alignment=TA_CENTER)
    normal = styles["Normal"]

    story = []
    tenant = reservation.tenant
    if tenant.logo:
        try:
            story.append(Image(tenant.logo.path, width=30 * mm, height=30 * mm))
        except Exception:
            pass

    story.append(Paragraph(tenant.nom_agence, title_style))
    story.append(Paragraph("CONTRAT DE LOCATION DE VEHICULE", styles["Heading2"]))
    story.append(Spacer(1, 6 * mm))

    infos = [
        ["Client", reservation.client.nom],
        ["Telephone / WhatsApp", reservation.client.telephone_whatsapp],
        ["CNI", reservation.client.cni or "-"],
        ["Vehicule", f"{reservation.vehicule.marque} {reservation.vehicule.modele}"],
        ["Immatriculation", reservation.vehicule.immatriculation],
        ["Date de depart", str(reservation.date_depart)],
        ["Date de retour prevue", str(reservation.date_retour)],
        ["Prix total", f"{reservation.prix_total} FCFA"],
        ["Caution", f"{reservation.vehicule.caution} FCFA"],
    ]
    table = Table(infos, colWidths=[60 * mm, 100 * mm])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
    ]))
    story.append(table)
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph("Conditions generales", styles["Heading3"]))
    conditions = (
        "Le locataire s'engage a restituer le vehicule a la date convenue, dans l'etat ou il l'a recu, "
        "carburant plein. Tout retard non signale a l'agence sera facture. La caution sera restituee "
        "apres inspection du vehicule au retour, deduction faite des eventuels frais de remise en etat "
        "ou de carburant manquant. Le locataire est responsable de toute infraction au code de la route "
        "commise durant la periode de location."
    )
    story.append(Paragraph(conditions, normal))
    story.append(Spacer(1, 20 * mm))

    signature = Table(
        [["Signature du client", "Signature de l'agence"], ["", ""]],
        colWidths=[80 * mm, 80 * mm], rowHeights=[8 * mm, 20 * mm],
    )
    signature.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LINEABOVE", (0, 1), (0, 1), 0.5, colors.black),
        ("LINEABOVE", (1, 1), (1, 1), 0.5, colors.black),
    ]))
    story.append(signature)

    doc.build(story)
    buffer.seek(0)
    return buffer
