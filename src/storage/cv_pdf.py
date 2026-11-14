"""Dynamic PDF CV generator using ReportLab for ATS candidate applications."""

import io
import os
import re
from typing import Dict, Any, Optional
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _safe(text: Any) -> str:
    """Escapes &, < and > so untrusted text can't be parsed as ReportLab Paragraph markup."""
    return _xml_escape(str(text))


def _init_fonts() -> tuple[str, str]:
    """Registers standard TrueType fonts for Vietnamese support if available on the system."""
    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"

    candidate_paths = [
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"),
        ("C:/Windows/Fonts/calibri.ttf", "C:/Windows/Fonts/calibrib.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]

    for reg_path, bold_path in candidate_paths:
        if os.path.exists(reg_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont("CustomSans", reg_path))
                pdfmetrics.registerFont(TTFont("CustomSans-Bold", bold_path))
                return "CustomSans", "CustomSans-Bold"
            except Exception:
                pass

    return font_name, font_bold


def generate_candidate_cv_pdf(
    app: Dict[str, Any],
    job: Optional[Dict[str, Any]] = None,
    blind_mode: bool = False,
) -> bytes:
    """Generates an A4 formatted PDF Curriculum Vitae for a candidate application."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    font_reg, font_bold = _init_fonts()
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CvName",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
    )

    subtitle_style = ParagraphStyle(
        "CvSubtitle",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4F46E5"),
    )

    contact_style = ParagraphStyle(
        "CvContact",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748B"),
    )

    section_heading = ParagraphStyle(
        "CvSectionHeading",
        parent=styles["Normal"],
        fontName=font_bold,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "CvBody",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )

    badge_style = ParagraphStyle(
        "CvBadge",
        parent=styles["Normal"],
        fontName=font_reg,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )

    story = []

    # 1. Header Information
    candidate_name = "[ỨNG VIÊN ẨN DANH / BLIND CANDIDATE]" if blind_mode else _safe(app.get("candidate_name", "Candidate"))
    current_title = _safe(app.get("current_title") or (job.get("title") if job else "Chuyên viên"))
    years = app.get("years_of_experience")
    years_text = f" &bull; {years} năm kinh nghiệm" if years else ""
    job_title = _safe(job.get("title") if job else app.get("job_title", ""))

    story.append(Paragraph(candidate_name, title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"{current_title}{years_text}", subtitle_style))
    story.append(Spacer(1, 4))

    contacts = []
    if not blind_mode:
        if app.get("email"):
            contacts.append(f"Email: {_safe(app['email'])}")
        if app.get("phone"):
            contacts.append(f"SĐT: {_safe(app['phone'])}")
        if app.get("location"):
            contacts.append(f"Địa điểm: {_safe(app['location'])}")
    else:
        contacts.append("Blind Mode ON: Thông tin cá nhân, tên tuổi, email, SĐT đã được ẩn tự động.")

    if job_title:
        contacts.append(f"Vị trí ứng tuyển: {job_title}")

    story.append(Paragraph(" &bull; ".join(contacts), contact_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceBefore=8, spaceAfter=10))

    # 2. AI Screening & Matching Summary Card
    ai_score = app.get("ai_score") or 0.0
    matched_skills = app.get("matched_skills") or []
    missing_skills = app.get("missing_skills") or []
    ai_rationale = app.get("ai_rationale") or ""

    if ai_score > 0 or matched_skills or missing_skills:
        ai_rows = [
            [
                Paragraph(f"<b>Điểm phù hợp AI:</b> <font color='#4F46E5'><b>{ai_score}%</b></font>", badge_style),
                Paragraph(
                    f"<b>Kỹ năng đạt:</b> <font color='#059669'>{len(matched_skills)} kỹ năng</font> &bull; "
                    f"<b>Kỹ năng thiếu:</b> <font color='#DC2626'>{len(missing_skills)} kỹ năng</font>",
                    badge_style,
                ),
            ]
        ]
        if ai_rationale:
            ai_rows.append([
                Paragraph(f"<b>Đánh giá sàng lọc:</b> {_safe(ai_rationale)}", badge_style),
                "",
            ])

        ai_table = Table(ai_rows, colWidths=[200, 320])
        ai_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("SPAN", (0, 1), (1, 1)) if ai_rationale else ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )
        story.append(ai_table)
        story.append(Spacer(1, 10))

    # 3. Technical Skills
    skills = app.get("skills") or []
    if skills:
        story.append(Paragraph("KỸ NĂNG CHUYÊN MÔN (TECHNICAL SKILLS)", section_heading))
        skills_str = " &bull; ".join(_safe(s) for s in skills)
        story.append(Paragraph(skills_str, body_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=6, spaceAfter=8))

    # 4. Work Experience & Resume Body Text
    story.append(Paragraph("KINH NGHIỆM LÀM VIỆC & CHI TIẾT CV (EXPERIENCE & DETAILS)", section_heading))

    if blind_mode:
        # Never fall back to resume_raw_text here — that would leak unredacted,
        # potentially identifying content into a CV that is supposed to be blind.
        raw_text = app.get("resume_redacted_text") or "Chưa có bản CV đã ẩn danh."
    else:
        raw_text = app.get("resume_raw_text") or "Chưa có thông tin văn bản CV."

    paragraphs = raw_text.split("\n\n")
    for para in paragraphs:
        cleaned = para.strip()
        if not cleaned:
            continue
        # Clean lines, then escape so markup-like characters in the resume text
        # (e.g. a literal "<" or "&") aren't parsed as ReportLab Paragraph markup.
        lines = [re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", l) for l in cleaned.split("\n")]
        line_text = "<br/>".join(_safe(l) for l in lines)
        story.append(Paragraph(line_text, body_style))
        story.append(Spacer(1, 5))

    doc.build(story)
    return buf.getvalue()
