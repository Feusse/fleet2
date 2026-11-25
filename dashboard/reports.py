"""Generation du rapport mensuel en PDF (ReportLab) et Excel (openpyxl)."""
from io import BytesIO
from datetime import date
from django.db.models import Sum
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import openpyxl
from openpyxl.styles import Font, PatternFill

from reservations.models import Reservation
from billing.models import Paiement


def _donnees_du_mois(tenant, annee, mois):
    reservations = Reservation.objects.filter(
        tenant=tenant, date_depart__year=annee, date_depart__month=mois
    ).select_related("client", "vehicule")

    paiements = Paiement.objects.filter(
        tenant=tenant, statut="paye", date_paiement__year=annee, date_paiement__month=mois
    ).select_related("reservation")

    ca_total = paiements.aggregate(total=Sum("montant"))["total"] or 0
    return reservations, paiements, ca_total


def generer_rapport_pdf(tenant, annee, mois):
    reservations, paiements, ca_total = _donnees_du_mois(tenant, annee, mois)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                             topMargin=16 * mm, bottomMargin=16 * mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Rapport mensuel - {tenant.nom_agence}", styles["Title"]),
        Paragraph(f"Periode : {mois:02d}/{annee}", styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph(f"Chiffre d'affaires encaisse : {ca_total} FCFA", styles["Heading3"]),
        Spacer(1, 6 * mm),
        Paragraph("Reservations du mois", styles["Heading3"]),
    ]

    data = [["Client", "Vehicule", "Depart", "Retour", "Prix", "Statut"]]
    for r in reservations:
        data.append([
            r.client.nom, str(r.vehicule), str(r.date_depart), str(r.date_retour),
            f"{r.prix_total} FCFA", r.get_statut_display(),
        ])
    if len(data) == 1:
        data.append(["Aucune reservation ce mois-ci.", "", "", "", "", ""])

    table = Table(data, colWidths=[35 * mm, 35 * mm, 22 * mm, 22 * mm, 25 * mm, 25 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Paiements encaisses", styles["Heading3"]))

    data2 = [["Reservation", "Type", "Methode", "Montant"]]
    for p in paiements:
        data2.append([str(p.reservation), p.get_type_paiement_display(), p.get_methode_display(), f"{p.montant} FCFA"])
    if len(data2) == 1:
        data2.append(["Aucun paiement ce mois-ci.", "", "", ""])

    table2 = Table(data2, colWidths=[55 * mm, 30 * mm, 30 * mm, 30 * mm])
    table2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table2)

    doc.build(story)
    buffer.seek(0)
    return buffer


def generer_rapport_excel(tenant, annee, mois):
    reservations, paiements, ca_total = _donnees_du_mois(tenant, annee, mois)
    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "Reservations"
    entete_style = Font(bold=True, color="FFFFFF")
    entete_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")

    ws1.append(["Client", "Telephone", "Vehicule", "Immatriculation", "Depart", "Retour", "Prix total", "Statut"])
    for cell in ws1[1]:
        cell.font = entete_style
        cell.fill = entete_fill
    for r in reservations:
        ws1.append([
            r.client.nom, r.client.telephone_whatsapp, str(r.vehicule), r.vehicule.immatriculation,
            str(r.date_depart), str(r.date_retour), float(r.prix_total or 0), r.get_statut_display(),
        ])

    ws2 = wb.create_sheet("Paiements")
    ws2.append(["Reservation", "Type", "Methode", "Montant", "Date"])
    for cell in ws2[1]:
        cell.font = entete_style
        cell.fill = entete_fill
    for p in paiements:
        ws2.append([
            str(p.reservation), p.get_type_paiement_display(), p.get_methode_display(),
            float(p.montant), p.date_paiement.strftime("%Y-%m-%d"),
        ])

    ws3 = wb.create_sheet("Resume")
    ws3.append(["Agence", tenant.nom_agence])
    ws3.append(["Periode", f"{mois:02d}/{annee}"])
    ws3.append(["Chiffre d'affaires encaisse (FCFA)", float(ca_total)])
    ws3.append(["Nombre de reservations", reservations.count()])

    for ws in (ws1, ws2, ws3):
        for col in ws.columns:
            longueur = max((len(str(c.value)) for c in col if c.value is not None), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(longueur + 2, 40)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
