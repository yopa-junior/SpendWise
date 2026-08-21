import uuid
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload  
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')  # Mode non interactif

from app.models.user import User
from app.models.notification import NotificationType
from app.services.statistics_service import StatisticsService
from app.services.budget_service import BudgetService
from app.services.wallet_service import WalletService
from app.services.notification_service import NotificationService
from app.notifications.email.mail import send_email
from app.repositories.budget_repository import BudgetRepository
from app.models.expense import Expense
from app.models.category import Category
from app.models.budget import Budget


def _previous_month_range(reference: date | None = None, periode: str = "current") -> tuple[date, date]:
    """Calcule le premier et dernier jour selon la période choisie."""
    reference = reference or date.today()
    if periode == "previous":
        # Mois précédent
        premier_jour_mois_actuel = reference.replace(day=1)
        dernier_jour_mois_precedent = premier_jour_mois_actuel - timedelta(days=1)
        premier_jour_mois_precedent = dernier_jour_mois_precedent.replace(day=1)
        return premier_jour_mois_precedent, dernier_jour_mois_precedent
    else:
        # Mois en cours (par défaut)
        premier_jour_mois = reference.replace(day=1)
        dernier_jour_mois = reference.replace(day=1, month=reference.month+1) - timedelta(days=1)
        return premier_jour_mois, dernier_jour_mois


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.statistics_service = StatisticsService(session)
        self.budget_service = BudgetService(session)
        self.wallet_service = WalletService(session)
        self.notification_service = NotificationService(session)
        self.budget_repo = BudgetRepository(session)

    async def generate_monthly_report_for_user(self, user: User, periode: str = "current") -> None:
        """Génère et envoie le résumé mensuel pour un utilisateur donné."""
        date_debut, date_fin = _previous_month_range(periode=periode)

        try:
            summary = await self.statistics_service.get_summary(user.id, date_debut, date_fin)
        except Exception:
            return

        mois_nom = date_debut.strftime("%B %Y")

        # --- 1. Notification in-app ---
        message = (
            f"Résumé de {mois_nom} : {summary.total_periode} {summary.devise} dépensés"
            + (f", principalement en {summary.categorie_principale_nom}." if summary.categorie_principale_nom else ".")
        )
        await self.notification_service.create_notification(
            user_id=user.id,
            type=NotificationType.RESUME_MENSUEL,
            titre=f"Ton résumé de {mois_nom}",
            message=message,
        )

        # --- 2. Générer le PDF complet ---
        pdf_buffer = await self._generate_pdf(user, summary, date_debut, date_fin, mois_nom)

        # --- 3. Envoyer l'email avec le PDF en pièce jointe ---
        evolution_signe = "+" if summary.evolution_pourcentage >= 0 else ""
        await send_email(
            subject=f"Ton résumé SpendWise de {mois_nom}",
            recipients=[user.email],
            template_name="monthly_report.html",
            template_body={
                "nom": user.nom,
                "mois": mois_nom,
                "total_depense": str(summary.total_periode),
                "devise": summary.devise,
                "categorie_principale": summary.categorie_principale_nom or "Aucune",
                "evolution_pourcentage": f"{evolution_signe}{summary.evolution_pourcentage}",
            },
            attachments=[("resume_mensuel.pdf", pdf_buffer.getvalue(), "application/pdf")],
        )

    async def generate_report_pdf(self, user: User, periode: str = "current") -> io.BytesIO:
        """Génère le PDF sans envoyer d'email (pour téléchargement direct)."""
        date_debut, date_fin = _previous_month_range(periode=periode)
        summary = await self.statistics_service.get_summary(user.id, date_debut, date_fin)
        mois_nom = date_debut.strftime("%B %Y")
        return await self._generate_pdf(user, summary, date_debut, date_fin, mois_nom)

    async def _generate_pdf(self, user: User, summary, date_debut: date, date_fin: date, mois_nom: str) -> io.BytesIO:
        """Génère un PDF complet avec toutes les sections."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # ===== Titre =====
        title_style = ParagraphStyle(
            name="Title",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            fontSize=24,
            textColor=colors.HexColor("#059669"),
        )
        story.append(Paragraph(f"Résumé mensuel - {mois_nom}", title_style))
        story.append(Spacer(1, 5 * mm))

        # ===== Informations utilisateur =====
        story.append(Paragraph(f"Utilisateur : {user.nom}", styles["Normal"]))
        story.append(Paragraph(f"Email : {user.email}", styles["Normal"]))
        story.append(Spacer(1, 5 * mm))

        # ===== Résumé global =====
        story.append(Paragraph("Résumé global", styles["Heading2"]))
        story.append(Spacer(1, 2 * mm))
        data = [
            [Paragraph("Total dépensé", styles["Normal"]), Paragraph(f"{summary.total_periode} {summary.devise}", styles["Normal"])],
            [Paragraph("Évolution vs mois précédent", styles["Normal"]), Paragraph(f"{summary.evolution_pourcentage}%", styles["Normal"])],
            [Paragraph("Catégorie principale", styles["Normal"]), Paragraph(summary.categorie_principale_nom or "Aucune", styles["Normal"])],
        ]
        table = Table(data, colWidths=[100*mm, 80*mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)
        story.append(Spacer(1, 10 * mm))

        # ===== Dépenses par catégorie =====
        story.append(Paragraph("Dépenses par catégorie", styles["Heading2"]))
        story.append(Spacer(1, 2 * mm))
        try:
            breakdown = await self.statistics_service.get_category_breakdown(user.id, date_debut, date_fin)
            if breakdown and breakdown.repartition:
                # Tableau des catégories
                cat_data = [
                    [Paragraph(cat.category_nom, styles["Normal"]), Paragraph(f"{cat.montant_total} {breakdown.devise}", styles["Normal"])]
                    for cat in breakdown.repartition
                ]
                cat_table = Table([["Catégorie", "Montant"]] + cat_data, colWidths=[100*mm, 80*mm])
                cat_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(cat_table)
                story.append(Spacer(1, 5 * mm))

                # Graphique en camembert
                fig, ax = plt.subplots(figsize=(6, 4))
                labels = [cat.category_nom for cat in breakdown.repartition]
                sizes = [cat.montant_total for cat in breakdown.repartition]
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                img_buf = io.BytesIO()
                plt.savefig(img_buf, format='png', bbox_inches='tight')
                plt.close()
                img_buf.seek(0)
                story.append(Image(img_buf, width=120*mm, height=80*mm))
            else:
                story.append(Paragraph("Aucune catégorie de dépense pour cette période.", styles["Normal"]))
        except Exception as e:
            print(f"❌ Erreur catégories : {e}")
            story.append(Paragraph("Erreur lors du chargement des catégories.", styles["Normal"]))
        story.append(Spacer(1, 10 * mm))

        # ===== Budgets =====
        story.append(Paragraph("Progression des budgets", styles["Heading2"]))
        story.append(Spacer(1, 2 * mm))
        try:
            # ✅ Charger les budgets AVEC les catégories associées
            stmt = select(Budget).where(Budget.user_id == user.id).options(joinedload(Budget.category))
            result = await self.session.execute(stmt)
            budgets = result.unique().scalars().all()

            if budgets:
                budget_data = []
                for budget in budgets:
                    progress = await self.budget_service.get_progress(budget.id, user.id)
                    # ✅ Récupérer le nom depuis la catégorie chargée, ou "Budget global"
                    if budget.category_id and budget.category:
                        budget_name = budget.category.nom
                    else:
                        budget_name = "Budget global"
                    budget_data.append([
                        Paragraph(budget_name, styles["Normal"]),
                        Paragraph(f"{progress.montant_depense} {progress.devise}", styles["Normal"]),
                        Paragraph(f"{progress.pourcentage}%", styles["Normal"]),
                    ])
                budget_table = Table([["Budget", "Dépensé", "Progression"]] + budget_data, colWidths=[70*mm, 60*mm, 50*mm])
                budget_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(budget_table)
            else:
                story.append(Paragraph("Aucun budget actif.", styles["Normal"]))
        except Exception as e:
            print(f"❌ Erreur budgets : {e}")
            story.append(Paragraph("Erreur lors du chargement des budgets.", styles["Normal"]))
        story.append(Spacer(1, 10 * mm))

        # ===== Portefeuilles =====
        story.append(Paragraph("Portefeuilles", styles["Heading2"]))
        story.append(Spacer(1, 2 * mm))
        try:
            wallets = await self.wallet_service.list_wallets(user.id)
            if wallets:
                wallet_data = [
                    [Paragraph(w.nom_wallet, styles["Normal"]), Paragraph(f"{w.solde} {w.devise}", styles["Normal"])]
                    for w in wallets
                ]
                wallet_table = Table([["Portefeuille", "Solde"]] + wallet_data, colWidths=[100*mm, 80*mm])
                wallet_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(wallet_table)
            else:
                story.append(Paragraph("Aucun portefeuille.", styles["Normal"]))
        except Exception as e:
            print(f"❌ Erreur portefeuilles : {e}")
            story.append(Paragraph("Erreur lors du chargement des portefeuilles.", styles["Normal"]))
        story.append(Spacer(1, 10 * mm))

        # ===== Top 5 des dépenses =====
        story.append(Paragraph("Top 5 des dépenses", styles["Heading2"]))
        story.append(Spacer(1, 2 * mm))
        try:
            # Requête SQL directe pour le Top 5
            query = (
                select(Expense, Category.nom.label('category_nom'))
                .join(Category, Expense.category_id == Category.id)
                .where(Expense.user_id == user.id)
                .where(Expense.date_depense.between(date_debut, date_fin))
                .order_by(Expense.montant.desc())
                .limit(5)
            )
            result = await self.session.execute(query)
            expenses = result.all()

            if expenses:
                expense_data = [
                    [Paragraph(e.Expense.description or "-", styles["Normal"]), 
                     Paragraph(e.category_nom, styles["Normal"]), 
                     Paragraph(f"{e.Expense.montant} {e.Expense.devise}", styles["Normal"])]
                    for e in expenses
                ]
                expense_table = Table([["Description", "Catégorie", "Montant"]] + expense_data, colWidths=[60*mm, 60*mm, 60*mm])
                expense_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(expense_table)
            else:
                story.append(Paragraph("Aucune dépense dans le top 5.", styles["Normal"]))
        except Exception as e:
            print(f"❌ Erreur top 5 : {e}")
            story.append(Paragraph("Erreur lors du chargement du top 5.", styles["Normal"]))
        story.append(Spacer(1, 10 * mm))

        # ===== Pied de page =====
        story.append(Paragraph("Généré par SpendWise", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return buffer