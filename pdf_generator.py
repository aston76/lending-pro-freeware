"""
Lending Pro Freeware — PDF Generator
Generates loan contracts and payment receipts using reportlab.
"""

import os
import io
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app_config import APP_NAME
from database import get_connection, dict_from_row, rows_to_list, APP_SUPPORT_DIR
from currency_utils import format_money, normalize_currency


def _get_styles():
    """Get custom paragraph styles."""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#334155'),
        alignment=TA_CENTER,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#475569'),
        spaceBefore=12,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='FieldLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748b')
    ))
    styles.add(ParagraphStyle(
        name='FieldValue',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold'
    ))
    styles.add(ParagraphStyle(
        name='SmallText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#94a3b8')
    ))
    return styles


def _get_company_info():
    """Get company info from settings."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings WHERE key IN ('company_name', 'company_address', 'company_contact', 'currency')")
    rows = cursor.fetchall()
    conn.close()
    info = {r['key']: r['value'] for r in rows}
    return {
        'name': info.get('company_name', APP_NAME),
        'address': info.get('company_address', ''),
        'contact': info.get('company_contact', ''),
        'currency': normalize_currency(info.get('currency', 'PHP')),
    }


def generate_contract_pdf(loan_id, output_path=None):
    """
    Generate a loan contract PDF.
    Saves to output_path and returns it. Returns None if loan not found.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get loan details
    cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    loan = dict_from_row(cursor.fetchone())
    if not loan:
        conn.close()
        return None

    # Get client details
    cursor.execute("SELECT * FROM clients WHERE id = ?", (loan['client_id'],))
    client = dict_from_row(cursor.fetchone())

    # Get amortization schedule
    cursor.execute(
        "SELECT * FROM amortization_schedule WHERE loan_id = ? ORDER BY month_number",
        (loan_id,)
    )
    schedule = rows_to_list(cursor.fetchall())
    conn.close()

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    company = _get_company_info()
    elements = []

    # Header
    # Include logo if available
    logo_path = os.path.join(APP_SUPPORT_DIR, "logo.png")
    if os.path.exists(logo_path):
        from reportlab.lib.utils import ImageReader
        try:
            img = ImageReader(logo_path)
            orig_w, orig_h = img.getSize()
            # Max width 40mm, max height 20mm
            target_h = 20 * mm
            target_w = (orig_w * target_h) / orig_h
            if target_w > 40 * mm:
                target_w = 40 * mm
                target_h = (orig_h * target_w) / orig_w
            elements.append(Image(logo_path, width=target_w, height=target_h, hAlign='LEFT'))
            elements.append(Spacer(1, 4*mm))
        except Exception:
            pass

    elements.append(Paragraph(company['name'], styles['CompanyName']))
    if company['address']:
        elements.append(Paragraph(company['address'], styles['SmallText']))
    if company['contact']:
        elements.append(Paragraph(company['contact'], styles['SmallText']))
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1')))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("LOAN AGREEMENT / CONTRACT", styles['DocTitle']))
    elements.append(Spacer(1, 4*mm))

    # Contract date
    elements.append(Paragraph(
        f"Date: {datetime.now().strftime('%B %d, %Y')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 4*mm))

    # Client information
    elements.append(Paragraph("BORROWER INFORMATION", styles['SectionHeader']))
    client_data = [
        ["Client ID:", client['id'], "Name:", f"{client['first_name']} {client['last_name']}"],
        ["Address:", client['address'], "Contact:", client['contact']],
    ]
    client_table = Table(client_data, colWidths=[70, 160, 70, 160])
    client_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#64748b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 4*mm))

    # Loan details
    elements.append(Paragraph("LOAN DETAILS", styles['SectionHeader']))
    interest_label = "Fixed" if loan['interest_type'] == 'fixed' else "Declining Balance"
    term_rate = float(loan['interest_rate'])
    original_term = int(loan.get('original_term_months') or loan['term_months'])
    monthly_rate = term_rate / max(original_term, 1)
    total_repayment = float(loan['principal']) + float(loan['total_interest'])
    loan_data = [
        ["Principal Amount:", format_money(loan['principal'], company['currency']), "Monthly Rate:", f"{monthly_rate:.2f}%"],
        ["Interest Type:", interest_label, "Term Rate:", f"{term_rate:.2f}%"],
        ["Term:", f"{loan['term_months']} months", "Monthly Payment:", format_money(loan['monthly_payment'], company['currency'])],
        ["Total Interest:", format_money(loan['total_interest'], company['currency']), "Total Repayment:", format_money(total_repayment, company['currency'])],
        ["Start Date:", loan['start_date'], "Status:", loan['status'].upper()],
    ]
    loan_table = Table(loan_data, colWidths=[100, 130, 100, 130])
    loan_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#64748b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(loan_table)
    elements.append(Spacer(1, 6*mm))

    # Amortization schedule
    elements.append(Paragraph("AMORTIZATION SCHEDULE", styles['SectionHeader']))
    amort_header = ["#", "Due Date", "Principal", "Interest", "Total Due", "Balance"]
    amort_data = [amort_header]
    for entry in schedule:
        amort_data.append([
            str(entry['month_number']),
            entry['due_date'],
            format_money(entry['principal_portion'], company['currency']),
            format_money(entry['interest_portion'], company['currency']),
            format_money(entry['total_due'], company['currency']),
            format_money(entry['balance_remaining'], company['currency'])
        ])

    amort_table = Table(amort_data, colWidths=[25, 75, 80, 70, 80, 80])
    amort_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(amort_table)
    elements.append(Spacer(1, 10*mm))

    # Terms
    elements.append(Paragraph("TERMS AND CONDITIONS", styles['SectionHeader']))
    terms = [
        "1. The borrower agrees to repay the loan according to the amortization schedule above.",
        "2. Late payments may incur additional charges as agreed upon.",
        "3. The borrower acknowledges receipt of the full principal amount.",
        "4. This agreement is binding upon signature by both parties.",
    ]
    for t in terms:
        elements.append(Paragraph(t, styles['Normal']))
        elements.append(Spacer(1, 2*mm))

    elements.append(Spacer(1, 15*mm))

    # Signature lines
    sig_data = [
        ["_________________________", "", "_________________________"],
        ["Borrower's Signature", "", "Lender's Signature"],
        [f"{client['first_name']} {client['last_name']}", "", company['name']],
    ]
    sig_table = Table(sig_data, colWidths=[180, 100, 180])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#64748b')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        buffer.close()
        return output_path
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')


def generate_receipt_pdf(payment_id, output_path=None):
    """
    Generate a payment receipt PDF.
    Saves to output_path and returns it. Returns None if payment not found.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get payment
    cursor.execute("SELECT * FROM payments WHERE id = ? AND voided_at IS NULL", (payment_id,))
    payment = dict_from_row(cursor.fetchone())
    if not payment:
        conn.close()
        return None

    # Get loan
    cursor.execute("SELECT * FROM loans WHERE id = ?", (payment['loan_id'],))
    loan = dict_from_row(cursor.fetchone())

    # Get client
    cursor.execute("SELECT * FROM clients WHERE id = ?", (loan['client_id'],))
    client = dict_from_row(cursor.fetchone())

    # Get total paid
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total_paid FROM payments WHERE loan_id = ? AND voided_at IS NULL",
        (payment['loan_id'],)
    )
    total_paid = cursor.fetchone()['total_paid']
    conn.close()

    total_due = loan['principal'] + loan['total_interest']
    remaining = total_due - total_paid

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=25*mm, rightMargin=25*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = _get_styles()
    company = _get_company_info()
    elements = []

    # Header
    logo_path = os.path.join(APP_SUPPORT_DIR, "logo.png")
    if os.path.exists(logo_path):
        from reportlab.lib.utils import ImageReader
        try:
            img = ImageReader(logo_path)
            orig_w, orig_h = img.getSize()
            target_h = 20 * mm
            target_w = (orig_w * target_h) / orig_h
            if target_w > 40 * mm:
                target_w = 40 * mm
                target_h = (orig_h * target_w) / orig_w
            elements.append(Image(logo_path, width=target_w, height=target_h, hAlign='LEFT'))
            elements.append(Spacer(1, 4*mm))
        except Exception:
            pass
            
    elements.append(Paragraph(company['name'], styles['CompanyName']))
    elements.append(Spacer(1, 3*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1')))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("OFFICIAL PAYMENT RECEIPT", styles['DocTitle']))
    elements.append(Spacer(1, 6*mm))

    # Receipt info
    info_data = [
        ["Receipt No:", f"RCT-{payment['id']:06d}", "Date:", payment['payment_date']],
        ["Client ID:", client['id'], "Name:", f"{client['first_name']} {client['last_name']}"],
        ["Loan ID:", str(loan['id']), "Method:", payment['payment_method'].upper()],
    ]
    info_table = Table(info_data, colWidths=[80, 150, 60, 150])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#64748b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # Payment summary
    elements.append(Paragraph("PAYMENT SUMMARY", styles['SectionHeader']))
    summary_data = [
        ["Amount Paid:", format_money(payment['amount'], company['currency'])],
        ["Total Loan Amount:", format_money(total_due, company['currency'])],
        ["Total Paid to Date:", format_money(total_paid, company['currency'])],
        ["Remaining Balance:", format_money(remaining, company['currency'])],
    ]
    summary_table = Table(summary_data, colWidths=[180, 180])
    summary_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (1, -1), (1, -1),
         colors.HexColor('#16a34a') if remaining <= 0 else colors.HexColor('#1e293b')),
    ]))
    elements.append(summary_table)

    if payment['notes']:
        elements.append(Spacer(1, 4*mm))
        elements.append(Paragraph(f"Notes: {payment['notes']}", styles['Normal']))

    elements.append(Spacer(1, 20*mm))

    # Signature
    elements.append(Paragraph("_________________________", styles['Normal']))
    elements.append(Paragraph("Authorized Signature", styles['FieldLabel']))

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(
        f"This receipt was generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        styles['SmallText']
    ))

    doc.build(elements)
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        buffer.close()
        return output_path
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')


def generate_amortization_pdf(loan_id, output_path=None):
    """
    Generate a standalone amortization schedule PDF.
    Color-coded: paid = green, overdue = red, future = light.
    Returns output_path if provided, else base64 string.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM loans WHERE id = ?", (loan_id,))
    loan = dict_from_row(cursor.fetchone())
    if not loan:
        conn.close()
        return None

    cursor.execute("SELECT * FROM clients WHERE id = ?", (loan['client_id'],))
    client = dict_from_row(cursor.fetchone())

    cursor.execute(
        "SELECT * FROM amortization_schedule WHERE loan_id = ? ORDER BY month_number",
        (loan_id,)
    )
    schedule = rows_to_list(cursor.fetchall())

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total_paid FROM payments WHERE loan_id = ? AND voided_at IS NULL",
        (loan_id,)
    )
    total_paid_row = cursor.fetchone()
    total_paid = total_paid_row['total_paid'] if total_paid_row else 0
    conn.close()

    today_str = datetime.now().strftime("%Y-%m-%d")
    total_due_loan = loan['principal'] + loan['total_interest']
    remaining_loan = max(0, total_due_loan - total_paid)

    # Build PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    styles = _get_styles()
    company = _get_company_info()
    elements = []

    # ─── Header ───────────────────────────────────────────────────
    logo_path = os.path.join(APP_SUPPORT_DIR, "logo.png")
    if os.path.exists(logo_path):
        from reportlab.lib.utils import ImageReader
        try:
            img = ImageReader(logo_path)
            ow, oh = img.getSize()
            th = 16 * mm
            tw = (ow * th) / oh
            if tw > 35 * mm:
                tw = 35 * mm
                th = (oh * tw) / ow
            elements.append(Image(logo_path, width=tw, height=th, hAlign='LEFT'))
            elements.append(Spacer(1, 3*mm))
        except Exception:
            pass

    elements.append(Paragraph(company['name'], styles['CompanyName']))
    elements.append(Spacer(1, 2*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1')))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("AMORTIZATION SCHEDULE", styles['DocTitle']))
    elements.append(Spacer(1, 3*mm))

    # ─── Loan Summary ─────────────────────────────────────────────
    interest_label = "Fixed Rate" if loan['interest_type'] == 'fixed' else "Declining Balance"
    term_rate = float(loan['interest_rate'])
    original_term = int(loan.get('original_term_months') or loan['term_months'])
    monthly_rate = term_rate / max(original_term, 1)
    pct_paid = (total_paid / total_due_loan * 100) if total_due_loan > 0 else 0

    summary_data = [
        [
            Paragraph("<b>Client:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{client['first_name']} {client['last_name']}</b> ({client['id']})", styles['FieldValue']),
            Paragraph("<b>Loan #:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{loan['id']}</b>", styles['FieldValue']),
        ],
        [
            Paragraph("<b>Principal:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{format_money(loan['principal'], company['currency'])}</b>", styles['FieldValue']),
            Paragraph("<b>Interest Type:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{interest_label}</b>", styles['FieldValue']),
        ],
        [
            Paragraph("<b>Monthly Rate:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{monthly_rate:.2f}%</b>", styles['FieldValue']),
            Paragraph("<b>Term Rate:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{term_rate:.2f}%</b>", styles['FieldValue']),
        ],
        [
            Paragraph("<b>Total Due:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{format_money(total_due_loan, company['currency'])}</b>", styles['FieldValue']),
            Paragraph("<b>Total Paid:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{format_money(total_paid, company['currency'])} ({pct_paid:.1f}%)</b>", styles['FieldValue']),
        ],
        [
            Paragraph("<b>Remaining:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{format_money(remaining_loan, company['currency'])}</b>", styles['FieldValue']),
            Paragraph("<b>Term:</b>", styles['FieldLabel']),
            Paragraph(f"<b>{loan['term_months']} months — Start: {loan['start_date']}</b>", styles['FieldValue']),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[65, 120, 65, 120])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 5*mm))

    # ─── Color legend ─────────────────────────────────────────────
    legend_data = [[
        Paragraph("■ Paid", ParagraphStyle('l1', parent=styles['SmallText'], textColor=colors.HexColor('#16a34a'))),
        Paragraph("■ Overdue", ParagraphStyle('l2', parent=styles['SmallText'], textColor=colors.HexColor('#dc2626'))),
        Paragraph("■ Today", ParagraphStyle('l3', parent=styles['SmallText'], textColor=colors.HexColor('#d97706'))),
        Paragraph("■ Upcoming", ParagraphStyle('l4', parent=styles['SmallText'], textColor=colors.HexColor('#64748b'))),
    ]]
    legend_table = Table(legend_data, colWidths=[80, 80, 80, 80])
    legend_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(legend_table)
    elements.append(Spacer(1, 3*mm))

    # ─── Schedule Table ───────────────────────────────────────────
    amort_header = ["#", "Due Date", "Principal", "Interest", "Total Due", "Balance", "Status"]
    amort_data = [amort_header]

    cumulative_paid = 0
    for entry in schedule:
        cumulative_paid += entry['total_due']
        is_past = entry['due_date'] <= today_str
        is_today = entry['due_date'] == today_str
        is_paid = total_paid >= cumulative_paid
        is_overdue = is_past and not is_today and not is_paid and loan['status'] == 'active'

        if is_today:
            status_text = "TODAY"
            row_bg = colors.HexColor('#fffbeb')
            status_color = colors.HexColor('#d97706')
        elif is_paid:
            status_text = "✓ PAID"
            row_bg = colors.HexColor('#f0fdf4')
            status_color = colors.HexColor('#16a34a')
        elif is_overdue:
            status_text = "OVERDUE"
            row_bg = colors.HexColor('#fff1f2')
            status_color = colors.HexColor('#dc2626')
        else:
            status_text = "Upcoming"
            row_bg = colors.white
            status_color = colors.HexColor('#94a3b8')

        amort_data.append([
            str(entry['month_number']),
            entry['due_date'],
            format_money(entry['principal_portion'], company['currency']),
            format_money(entry['interest_portion'], company['currency']),
            format_money(entry['total_due'], company['currency']),
            format_money(entry['balance_remaining'], company['currency']),
            Paragraph(f"<b>{status_text}</b>", ParagraphStyle(
                f's_{entry["month_number"]}',
                parent=styles['SmallText'],
                textColor=status_color,
                alignment=TA_CENTER
            ))
        ])

    amort_table = Table(amort_data, colWidths=[18, 62, 62, 58, 62, 68, 50],
                        repeatRows=1)

    table_style = [
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        # Data rows
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (5, -1), 'RIGHT'),
        ('ALIGN', (6, 1), (6, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]

    # Apply row background colors
    cumulative_paid = 0
    for i, entry in enumerate(schedule, start=1):
        cumulative_paid += entry['total_due']
        is_past = entry['due_date'] <= today_str
        is_today = entry['due_date'] == today_str
        is_paid = total_paid >= cumulative_paid
        is_overdue = is_past and not is_today and not is_paid and loan['status'] == 'active'

        if is_today:
            row_bg = colors.HexColor('#fffbeb')
        elif is_paid:
            row_bg = colors.HexColor('#f0fdf4')
        elif is_overdue:
            row_bg = colors.HexColor('#fff1f2')
        else:
            row_bg = colors.white if i % 2 == 0 else colors.HexColor('#f8fafc')

        table_style.append(('BACKGROUND', (0, i), (-1, i), row_bg))

    amort_table.setStyle(TableStyle(table_style))
    elements.append(amort_table)

    # Footer
    elements.append(Spacer(1, 5*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} - {APP_NAME}",
        styles['SmallText']
    ))

    doc.build(elements)
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        buffer.close()
        return output_path
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode('utf-8')
