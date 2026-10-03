"""
Generates the full CEP report as a .docx with formal page border,
coloured heading bars, boxed quotations, framed certificates,
banded tables, and embedded field-visit photos.

Run:  python generate_report.py

Requires: python-docx, pillow

Assets:
    static/logo.png
    static/report_photos/record_01.jpg ... record_04.jpg
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT   = Path(__file__).parent
LOGO   = ROOT / "static" / "logo.png"
PHOTOS = ROOT / "static" / "report_photos"
OUT    = ROOT / "CEP_Report_Technical_Support_Rural_Startups.docx"

if not LOGO.exists():
    raise SystemExit(f"!! Logo not found at {LOGO}")

INDIGO = "1E1B4B"
GOLD   = "C88A1E"
RUST   = "B4502E"

doc = Document()


# ==================================================================
# GLOBAL STYLES
# ==================================================================
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)

rpr = normal.element.get_or_add_rPr()
rFonts = rpr.find(qn("w:rFonts"))
if rFonts is None:
    rFonts = OxmlElement("w:rFonts"); rpr.append(rFonts)
for a in ("w:ascii", "w:hAnsi", "w:cs"):
    rFonts.set(qn(a), "Times New Roman")

for lvl, size in [(1, 18), (2, 15), (3, 13)]:
    h = doc.styles[f"Heading {lvl}"]
    h.font.name = "Times New Roman"
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = RGBColor.from_string(INDIGO)
    h.paragraph_format.space_before = Pt(16)
    h.paragraph_format.space_after  = Pt(8)


# ==================================================================
# LOW-LEVEL XML HELPERS
# ==================================================================
def _shade(el, hex_fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    el.append(shd)


def shade_paragraph(paragraph, hex_fill):
    shade_paragraph_pPr(paragraph._p.get_or_add_pPr(), hex_fill)


def shade_paragraph_pPr(pPr, hex_fill):
    _shade(pPr, hex_fill)


def shade_cell(cell, hex_fill):
    _shade(cell._tc.get_or_add_tcPr(), hex_fill)


def border_paragraph(paragraph, sides="all", color=GOLD, sz=8, space=6):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    side_list = ["top", "left", "bottom", "right"] if sides == "all" else [sides]
    for side in side_list:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), str(sz))
        b.set(qn("w:space"), str(space))
        b.set(qn("w:color"), color)
        pBdr.append(b)
    pPr.append(pBdr)


def border_cell(cell, sides="all", color=INDIGO, sz=8):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    side_list = ["top", "left", "bottom", "right"] if sides == "all" else [sides]
    for side in side_list:
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), str(sz))
        b.set(qn("w:color"), color)
        tcBorders.append(b)
    tcPr.append(tcBorders)


def add_page_border(section, style="thinThickSmallGap",
                    sz="12", space="24", color=INDIGO):
    """
    Add a formal page border to every page of this section.

    style : 'single' | 'double' | 'thinThickSmallGap'
            | 'thinThickThinSmallGap' | 'thickThick'
    sz    : line thickness in eighths of a point (12 = 1.5pt)
    space : distance from the page edge, in points (max 31)
    color : hex colour, no leading '#'
    """
    sectPr = section._sectPr

    # Clear any previously set border
    for old in sectPr.findall(qn("w:pgBorders")):
        sectPr.remove(old)

    pgBorders = OxmlElement("w:pgBorders")
    pgBorders.set(qn("w:offsetFrom"), "page")
    pgBorders.set(qn("w:display"),    "allPages")

    for edge in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"),   style)
        e.set(qn("w:sz"),    sz)
        e.set(qn("w:space"), space)
        e.set(qn("w:color"), color)
        pgBorders.append(e)

    # Must sit immediately after pgMar inside sectPr
    pgMar = sectPr.find(qn("w:pgMar"))
    if pgMar is not None:
        pgMar.addnext(pgBorders)
    else:
        sectPr.append(pgBorders)


def add_hr(paragraph, color=GOLD, sz=12):
    border_paragraph(paragraph, sides="bottom", color=color, sz=sz, space=2)


def ornament():
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    r = p.add_run("\u25C6   \u25C6   \u25C6")
    r.font.color.rgb = RGBColor.from_string(GOLD)
    r.font.size = Pt(10)
    return p


# ==================================================================
# CONTENT HELPERS
# ==================================================================
def centre(text="", bold=False, italic=False, size=12, space_after=6, color=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)
    return p


def para(text, bold=False, italic=False, indent=None, size=None, color=None):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent  = Inches(indent)
        p.paragraph_format.right_indent = Inches(indent)
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:  r.font.size = Pt(size)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    return p


def bullets(items):
    for it in items:
        p = doc.add_paragraph(it, style="List Bullet")
        p.paragraph_format.line_spacing = 1.4


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def bar_heading(text, level=2, color=INDIGO, text_color="FFFFFF"):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after  = Pt(8)
    p.paragraph_format.left_indent  = Inches(0.08)
    p.paragraph_format.right_indent = Inches(0.08)
    r = p.add_run("  " + text + "  ")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(14 if level == 2 else 12)
    r.font.color.rgb = RGBColor.from_string(text_color)
    shade_paragraph(p, color)
    return p


def section_title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(16)
    r = p.add_run(text)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor.from_string(INDIGO)
    add_hr(p, color=GOLD, sz=14)
    return p


def quote_box(quote):
    tbl = doc.add_table(rows=1, cols=1); tbl.autofit = True
    cell = tbl.rows[0].cells[0]
    shade_cell(cell, "FFF8E7")
    border_cell(cell, "all", color=GOLD, sz=10)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after  = Pt(6)
    r = p.add_run(quote)
    r.italic = True
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor.from_string(RUST)
    doc.add_paragraph()


def add_photo(filename, caption, width=Inches(5.0)):
    path = PHOTOS / filename
    if not path.exists():
        print(f"  [--] missing: {path}")
        return
    tbl = doc.add_table(rows=1, cols=1); tbl.autofit = True
    cell = tbl.rows[0].cells[0]
    border_cell(cell, "all", color=INDIGO, sz=14)
    shade_cell(cell, "FFFFFF")
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(path), width=width)
    c = doc.add_paragraph(caption)
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.runs[0].italic = True
    c.runs[0].font.size = Pt(10)
    c.runs[0].font.color.rgb = RGBColor.from_string("555555")
    doc.add_paragraph()


def add_page_numbers(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Page "); r.font.size = Pt(10); r.font.name = "Times New Roman"
    f1 = OxmlElement("w:fldSimple"); f1.set(qn("w:instr"), "PAGE"); p._p.append(f1)
    r2 = p.add_run(" of "); r2.font.size = Pt(10)
    f2 = OxmlElement("w:fldSimple"); f2.set(qn("w:instr"), "NUMPAGES"); p._p.append(f2)


def info_table(rows, accent=INDIGO):
    tbl = doc.add_table(rows=len(rows), cols=2); tbl.autofit = True
    for i, (k, v) in enumerate(rows):
        kc, vc = tbl.rows[i].cells
        kc.text = k; vc.text = v
        shade_cell(kc, accent)
        kc.paragraphs[0].runs[0].bold = True
        kc.paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string("FFFFFF")
        border_cell(kc, "all", color=accent, sz=8)
        border_cell(vc, "all", color=accent, sz=8)
    doc.add_paragraph()


# ##################################################################
# #                     COVER PAGE                                 #
# ##################################################################
centre("A Community Engagement Project Report", size=13, space_after=18, color=RUST)
centre("On", size=13, space_after=18)
centre('"TECHNICAL SUPPORT FOR RURAL STARTUPS"',
       bold=True, size=22, space_after=30, color=INDIGO)

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("\u2014 \u25C6 \u2014")
r.font.color.rgb = RGBColor.from_string(GOLD); r.font.size = Pt(14)

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(LOGO), width=Inches(1.7))

centre("Submitted by", size=12, space_after=14)
centre("Mergu Pravin Madhukar", bold=True, size=15, space_after=4, color=INDIGO)
centre("Mourya Chandar",        bold=True, size=15, space_after=26, color=INDIGO)

centre("In partial fulfilment for the award of the degree of", size=12, space_after=8)
centre("THIRD YEAR BACHELOR OF SCIENCE", bold=True, size=14, space_after=4, color=RUST)
centre("In", size=12, space_after=4)
centre("INFORMATION TECHNOLOGY", bold=True, size=14, space_after=26, color=RUST)

centre("Under the guidance of", size=12, space_after=6)
centre("Mrs. Hera Kausar", bold=True, size=15, space_after=26, color=INDIGO)

centre("Department of Information Technology", size=12, space_after=6)
centre("B.N.N. College (A.S. & C.), Bhiwandi", size=12, space_after=6)
centre("Semester V  |  Academic Year 2026\u20132027", size=12, space_after=4)
centre("September 2026", size=12, color=RUST)
page_break()


# ##################################################################
# #                     CERTIFICATE 1                              #
# ##################################################################
section_title("CERTIFICATE BY THE INSTITUTE")
tbl = doc.add_table(rows=1, cols=1); tbl.autofit = True
cell = tbl.rows[0].cells[0]
border_cell(cell, "all", color=GOLD, sz=18)
shade_cell(cell, "FFFDF5")
p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(10)
r = p.add_run("CERTIFICATE")
r.bold = True; r.font.size = Pt(16); r.font.color.rgb = RGBColor.from_string(INDIGO)

body = cell.add_paragraph(
    "This is to certify that Mr. Mergu Pravin Madhukar and Mr. Mourya Chandar, "
    "of T.Y. B.Sc. (Information Technology) (Semester V) class have satisfactorily "
    "completed the Community Engagement Project Report on \u201cTechnical Support for "
    "Rural Startups\u201d to be submitted in the partial fulfilment for the award of "
    "Third Year Bachelor of Science in Information Technology during the academic "
    "year 2026\u20132027."
)
body.paragraph_format.space_before = Pt(6)
body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

cell.add_paragraph()
cell.add_paragraph("Date of Submission:  ____________________")
cell.add_paragraph("Place: Bhiwandi")
cell.add_paragraph()
sig = cell.add_paragraph("                                        Signature of Principal")
sig.runs[0].bold = True
page_break()


# ##################################################################
# #                     CERTIFICATE 2                              #
# ##################################################################
section_title("CERTIFICATE BY THE MENTOR")
tbl = doc.add_table(rows=1, cols=1); tbl.autofit = True
cell = tbl.rows[0].cells[0]
border_cell(cell, "all", color=GOLD, sz=18)
shade_cell(cell, "FFFDF5")
p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("CERTIFICATE OF GUIDANCE")
r.bold = True; r.font.size = Pt(16); r.font.color.rgb = RGBColor.from_string(INDIGO)

b1 = cell.add_paragraph(
    "This is to certify that the Community Engagement Project Report entitled "
    "\u201cTechnical Support for Rural Startups\u201d is a bona fide record of work "
    "carried out by Mergu Pravin Madhukar and Mourya Chandar, students of T.Y. B.Sc. "
    "(Information Technology), under my guidance and supervision, in partial "
    "fulfilment of the requirements for the award of the degree of Third Year "
    "Bachelor of Science in Information Technology, University of Mumbai, during "
    "the academic year 2026\u20132027."
)
b1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
b2 = cell.add_paragraph(
    "The work presented in this report is original and has been carried out under "
    "my direct guidance. It has not been submitted elsewhere for the award of any "
    "other degree or diploma."
)
b2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
cell.add_paragraph()
cell.add_paragraph("Place: Bhiwandi")
cell.add_paragraph("Date:  ____________________")
cell.add_paragraph()
sig = cell.add_paragraph("                                        Mrs. Hera Kausar (Project Mentor)")
sig.runs[0].bold = True
page_break()


# ##################################################################
# #                     ACKNOWLEDGEMENT                            #
# ##################################################################
section_title("ACKNOWLEDGEMENT")
for t in [
    "We would like to extend our heartfelt thanks with a deep sense of gratitude and "
    "respect to everyone who provided us immense help and guidance during our field "
    "project work. We would like to thank our project mentor, Mrs. Hera Kausar, for "
    "providing constant direction, valuable suggestions, and a clear vision about the project.",
    "We have greatly benefited from her regular critical reviews and inspiration "
    "throughout our work. We are grateful to her for the guidance, encouragement, "
    "understanding and insightful support extended during every stage of the project, "
    "from planning the field visits to reviewing our final analysis.",
    "We would also like to thank our college for providing the required resources "
    "whenever needed and for giving us the opportunity to carry out this project. We "
    "would like to express our sincere thanks to our Principal I/C, Dr. Shashikant "
    "Mhalunkar, and our Head of Department, Mr. Pramod L. Shewale, for having facilitated "
    "us with the essential infrastructure and resources without which this project would "
    "not have been possible. We are also thankful to the entire staff of the Information "
    "Technology Department for their constant encouragement, suggestions, and moral "
    "support throughout the duration of our project.",
    "We sincerely thank all the rural entrepreneurs and startup owners who participated "
    "in our field visits and gave their honest and valuable responses, without which "
    "this study could not have been completed. Last but not the least, we would like "
    "to mention that we are greatly indebted to our friends and everybody who has been "
    "associated with our project at any stage but whose name does not find a place in "
    "this acknowledgement.",
]:
    p = doc.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
doc.add_paragraph()
para("With Sincere Regards,", bold=True)
para("Mergu Pravin Madhukar")
para("Mourya Chandar")
page_break()


# ##################################################################
# #                     ABSTRACT                                   #
# ##################################################################
section_title("ABSTRACT")
for t in [
    "The Technical Support for Rural Startups project was conducted as a Community "
    "Engagement Program (CEP) initiative to provide hands-on digital interventions to "
    "micro-businesses in villages near Bhiwandi, Maharashtra. The study combined field "
    "visits, direct technical training, and the development of practical software tools "
    "to help rural entrepreneurs adopt digital technologies for payments, inventory "
    "management, online discoverability, and photo processing.",
    "The project involved a structured visit model for each enterprise: a needs "
    "assessment where the team sat with the owner to understand their daily operations, "
    "a hands-on session where the team and the owner set up the appropriate tools "
    "together, and a follow-up review to see which habits survived.",
    "Four enterprises were visited across Bhiwandi and the surrounding villages: "
    "Srividyaniketan Classes in Bhiwandi, Baba ID Cards Solutions in Shelar, V Tech ID "
    "Solutions in Kariwali, and Digital ID Solutions in Khoni Gaon. The challenges ranged "
    "from administrative record-keeping in a coaching institute to repetitive batch photo "
    "processing for school-photography businesses.",
    "Three software tools were developed to address recurring friction points identified "
    "across the visits: an auto face-and-shoulder cropping tool built with RetinaFace and "
    "Pillow, a bulk background removal utility using the withoutbg model, and an Android "
    "smart camera renamer that names captured photos in DSLR-style sequence.",
    "A companion Flask-based web application was deployed at "
    "https://cep-project-python.onrender.com to document the entire project. The website "
    "includes a dashboard of field visit records, a resource library with downloadable "
    "training materials, and a demos page with embedded video walkthroughs. All field "
    "data is stored in a MySQL database and rendered dynamically.",
    "The project demonstrated that direct, hands-on support overcomes the initial "
    "hesitation that one-off workshops cannot. Follow-up visits proved essential for "
    "sustaining new digital habits, and interventions succeeded most when they matched "
    "each enterprise\u2019s existing record-keeping habits rather than replacing them "
    "outright.",
]:
    p = doc.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
page_break()


# ##################################################################
# #                     TABLE OF CONTENTS                          #
# ##################################################################
section_title("TABLE OF CONTENTS")
entries = [
    ("1.", "Introduction", 0),
    ("",   "1.1  Purpose of the Visit", 1),
    ("",   "1.2  Background Information", 1),
    ("",   "1.3  Scope of the Report", 1),
    ("2.", "Literature Review", 0),
    ("",   "2.1  Introduction", 1),
    ("",   "2.2  Previous Studies", 1),
    ("",   "2.3  Research Gap", 1),
    ("3.", "Methodology", 0),
    ("",   "3.1  Approach and Tools Used", 1),
    ("",   "3.2  Rationale Behind the Methods", 1),
    ("",   "3.3  Data Collection and Analysis", 1),
    ("",   "3.4  Limitations", 1),
    ("4.", "Field Work Descriptions, Observations and Analysis", 0),
    ("",   "4.1  Overview of Field Work", 1),
    ("",   "4.2  Detailed Field Visit Records", 1),
    ("",   "     4.2.1  Srividyaniketan Classes, Bhiwandi", 2),
    ("",   "     4.2.2  Baba ID Cards Solutions, Shelar", 2),
    ("",   "     4.2.3  V Tech ID Solutions, Kariwali", 2),
    ("",   "     4.2.4  Digital ID Solutions, Khoni Gaon", 2),
    ("",   "4.3  Cross-Cutting Observations", 1),
    ("",   "4.4  Product Demos \u2014 Software Tools Developed", 1),
    ("",   "4.5  Project Website \u2014 Deployment and Features", 1),
    ("5.", "Conclusion and Recommendations", 0),
    ("",   "5.1  Conclusion", 1),
    ("",   "5.2  Key Findings", 1),
    ("",   "5.3  Significance of Findings", 1),
    ("",   "5.4  Recommendation", 1),
    ("",   "5.5  Final Remark", 1),
    ("",   "References", 0),
    ("",   "Appendices", 0),
]
for num, title, depth in entries:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.left_indent = Inches(0.2 + 0.35 * depth)
    r = p.add_run(f"{num}  {title}" if num else title)
    r.font.size = Pt(12)
    if num:
        r.bold = True
        r.font.color.rgb = RGBColor.from_string(INDIGO)
page_break()


# ##################################################################
# #                     CHAPTER 1                                  #
# ##################################################################
section_title("CHAPTER 1  \u2014  INTRODUCTION")

bar_heading("1.1  Purpose of the Visit")
para(
    "The main purpose of our field project was to provide direct, hands-on technical "
    "support to micro-businesses and startups operating in villages near Bhiwandi, "
    "Maharashtra. The goal was to help rural entrepreneurs adopt digital tools for "
    "payments, inventory tracking, online presence, and everyday business operations "
    "\u2014 technologies that urban businesses take for granted but that often remain "
    "out of reach for village enterprises due to a lack of hands-on guidance."
)
para(
    "Rural micro-enterprises in India operate under conditions that make digital "
    "adoption unusually difficult. Unlike urban businesses, they cannot rely on nearby "
    "training centres, stable high-speed internet, or a peer network that is already "
    "fluent in digital tools. The gap is not one of awareness but of access to patient, "
    "personalised guidance."
)
para("The specific objectives of our field project were:", bold=True)
bullets([
    "To assess digital readiness: Evaluate each enterprise\u2019s existing record-keeping "
    "habits, payment methods, familiarity with digital tools, and comfort with smartphones.",
    "To provide practical training: Set up tools such as UPI, WhatsApp Business catalogues, "
    "Google Business Profiles, and Excel-based inventory trackers together with the owner, "
    "at their counter, on their own device.",
    "To build purpose-built tools: Develop simple software utilities that address the "
    "specific friction points observed during field visits, where no existing tool fit "
    "the workflow.",
    "To evaluate real adoption: Return after one week to check which habits actually "
    "carried over once the students left.",
    "To document findings: Record founder statements, before/after status, visit photos, "
    "and metadata for every enterprise visited.",
    "To deploy a public record: Build and host a web application that presents the entire "
    "project \u2014 field records, training resources, and software demos \u2014 accessible "
    "to anyone.",
])

bar_heading("1.2  Background Information")
para(
    "Digital adoption among rural micro-enterprises is a well-known challenge in India\u2019s "
    "development discourse. Government schemes such as Digital India and the UPI payment "
    "network have dramatically lowered the technical barriers to entry, but lowering a "
    "barrier is not the same as crossing it. A farmer or shopkeeper still needs someone "
    "to sit beside them, on their phone, and walk through the first few transactions "
    "before the tool becomes a habit."
)
para("Maintaining good digital practices matters because:", bold=True)
bullets([
    "Payments: UPI eliminates the need for exact change, reduces cash-handling risk, and "
    "enables sales from customers who may not carry cash.",
    "Discoverability: A Google Business Profile with an accurate GPS pin lets customers "
    "outside the village find the shop on Search and Maps.",
    "Inventory: A simple spreadsheet prevents stock-outs and over-ordering, both of which "
    "cost money and reputation.",
    "Photo quality: Clean product photos and consistently cropped ID-card photographs are "
    "essential for businesses whose output is visual.",
])

bar_heading("1.3  Scope of the Report")
para(
    "This report is based on information collected through field visits, hands-on training "
    "sessions, founder interviews, and the development of software prototypes. It includes "
    "the project objectives, background, detailed field visit records, software demos, "
    "project website documentation, analysis, recommendations, and limitations."
)
page_break()


# ##################################################################
# #                     CHAPTER 2                                  #
# ##################################################################
section_title("CHAPTER 2  \u2014  LITERATURE REVIEW")

bar_heading("2.1  Introduction")
para(
    "The literature on rural digital adoption in India has grown considerably over the "
    "past decade. Most studies agree on a common theme: awareness of digital tools is "
    "not the same as adoption, and adoption is not the same as sustained use. The gap "
    "between these three states is where field-level interventions matter most."
)

bar_heading("2.2  Previous Studies")
para(
    "Reports from the Telecom Regulatory Authority of India and NASSCOM have repeatedly "
    "shown that rural internet penetration has risen sharply, but business use of digital "
    "tools lags behind personal use. Studies of UPI adoption in tier-3 towns consistently "
    "find that the first successful transaction is the single biggest predictor of "
    "continued use \u2014 which validates the hands-on-first approach adopted in this project."
)
para(
    "Research on micro-enterprise digitisation has also emphasised fit over sophistication. "
    "Tools that match an owner\u2019s existing workflow are adopted far more readily than "
    "tools that require a complete change of habit."
)

bar_heading("2.3  Research Gap")
para(
    "What is less documented is the day-to-day reality of a technical support visit \u2014 "
    "the specific friction points that emerge only when you sit with an entrepreneur and "
    "watch them work. This report aims to contribute to that gap by documenting four such "
    "visits in detail, along with the purpose-built tools that resulted."
)
page_break()


# ##################################################################
# #                     CHAPTER 3                                  #
# ##################################################################
section_title("CHAPTER 3  \u2014  METHODOLOGY")

bar_heading("3.1  Approach and Tools Used")
para(
    "The project used a mixed-method approach combining qualitative observation with "
    "quantitative documentation. Each enterprise was visited in person, and the interaction "
    "proceeded through a fixed sequence: initial conversation, observation of the daily "
    "workflow, identification of the friction point, and collaborative setup or development "
    "of the solution."
)
bullets([
    "Direct observation of the founder\u2019s daily operations, record-keeping, and payment methods.",
    "Semi-structured interviews to understand the founder\u2019s stated pain points.",
    "Hands-on setup of digital tools, performed on the founder\u2019s own device.",
    "Development of purpose-built software where no existing tool fit the workflow.",
    "Photographic documentation of the visit, with the founder\u2019s consent.",
    "A structured database and website to record and publish the outcomes.",
])

bar_heading("3.2  Rationale Behind the Methods")
para(
    "Each method was chosen for a specific reason. Observation captured details that "
    "founders would not think to mention \u2014 the specific app they hesitated on, the "
    "physical folder of paper receipts, the manual step they repeated a hundred times a "
    "day. Interviews captured the founder\u2019s own framing of the problem. Hands-on setup "
    "ensured the founder saw the tool working on their own data. And purpose-built "
    "development addressed cases where the existing tool ecosystem simply did not cover "
    "the workflow."
)

bar_heading("3.3  Data Collection and Analysis")
para(
    "Data was collected through handwritten notes, photographs, and a structured form "
    "filled out during or immediately after each visit. Analysis was thematic \u2014 looking "
    "across the four visits for recurring patterns in the type of problem, the founder\u2019s "
    "response to the intervention, and the extent to which the solution was actually adopted."
)

bar_heading("3.4  Limitations")
bullets([
    "The sample size of four enterprises is small and should not be treated as representative.",
    "Follow-up was limited to a short window; longer-term adoption was not tracked.",
    "Self-reported statements from founders were not independently verified.",
    "The interventions were tailored to each enterprise; generalisation requires care.",
])
page_break()


# ##################################################################
# #                     CHAPTER 4                                  #
# ##################################################################
section_title("CHAPTER 4  \u2014  FIELD WORK")

bar_heading("4.1  Overview of Field Work")
para(
    "The field work for the Technical Support for Rural Startups project was carried out "
    "across four enterprises in Bhiwandi and the surrounding villages of Shelar, Kariwali, "
    "and Khoni Gaon during the months of September and October 2026. The team consisted "
    "of two students from T.Y. B.Sc. Information Technology, working under the guidance "
    "of the project mentor."
)
para(
    "Each visit followed a consistent three-stage structure. In the first stage, the team "
    "sat with the founder and observed their daily operations without any agenda. In the "
    "second stage, the team and the founder identified the single most significant friction "
    "point in their workflow. In the third stage, the solution \u2014 whether an existing "
    "tool or a purpose-built one \u2014 was demonstrated and deployed on the founder\u2019s "
    "own device before the team left."
)
para(
    "A recurring observation across all four visits was that the founders were not lacking "
    "in awareness of digital tools. They were already aware of the general category of "
    "solution they needed. What they lacked was the specific technical know-how to set it "
    "up, or a tool that fit their exact workflow."
)
ornament()


# -------------------- RECORD 01 --------------------
bar_heading("4.2.1  Record 01 \u2014 Srividyaniketan Classes, Bhiwandi", color=RUST)
info_table([
    ("Startup Name", "Srividyaniketan Classes"),
    ("Founder", "Niraj"),
    ("Village", "Bhiwandi"),
    ("Date of Visit", "03 October 2026"),
    ("Time of Visit", "11:20 AM"),
])
para("Background of the Enterprise", bold=True, color=INDIGO)
para(
    "Srividyaniketan Classes is a coaching institute located in Bhiwandi. The institute "
    "conducts regular classes for students in multiple subjects and manages a small "
    "teaching staff along with its student body. Like many coaching institutes of its "
    "size, most of its administrative work has traditionally been handled manually, with "
    "separate registers for attendance, fee collection, and internal records."
)
para("Observed Friction Point", bold=True, color=INDIGO)
para(
    "During the visit, it became clear that the institute\u2019s administrative burden "
    "fell almost entirely on the founder. Attendance for every student and teacher was "
    "tracked on paper registers, and there was no centralised record of the installments "
    "paid by students. When a parent enquired about their child\u2019s fee status, the "
    "founder had to manually cross-check multiple registers."
)
para("Founder\u2019s Own Statement", bold=True, color=INDIGO)
quote_box(
    "\u201cHas to manually track the attendance of every student and teacher, and there "
    "is no track of installments paid by the students. The founder wants to upload the "
    "marks online so they are accessible anywhere.\u201d"
)
para("Solution Designed", bold=True, color=INDIGO)
para(
    "A class management web application was built to centralise the institute\u2019s "
    "administrative operations. The system tracks attendance, fee installments, student "
    "marks, and basic student records in a single dashboard, accessible from any "
    "smartphone or browser."
)
para("Outcome", bold=True, color=INDIGO)
para(
    "The web application was demonstrated and handed over during the visit. The founder "
    "was able to log in, register a student, mark attendance, and record a fee installment "
    "in the same session."
)
add_photo("record_01.jpg",
          "Figure 4.1 \u2014 Field visit to Srividyaniketan Classes, Bhiwandi.")
ornament()


# -------------------- RECORD 02 --------------------
bar_heading("4.2.2  Record 02 \u2014 Baba ID Cards Solutions, Shelar", color=RUST)
info_table([
    ("Startup Name", "Baba ID Cards Solutions"),
    ("Founder", "Shridhar Siripuram"),
    ("Village", "Shelar"),
    ("Date of Visit", "29 September 2026"),
    ("Time of Visit", "01:14 PM"),
])
para("Background of the Enterprise", bold=True, color=INDIGO)
para(
    "Baba ID Cards Solutions operates a school-photography business. The founder travels "
    "to schools across the Bhiwandi region to photograph students for ID cards, school "
    "records, and yearbooks. Each school visit produces hundreds of photographs, which "
    "need to be transferred, sorted, and named before delivery."
)
para("Observed Friction Point", bold=True, color=INDIGO)
para(
    "The founder\u2019s workflow relied on a DSLR camera and a laptop. After each school "
    "visit, the raw photographs were transferred to the computer, and the founder had to "
    "rename them manually one by one to keep them in a consistent sequence."
)
para("Founder\u2019s Own Statement", bold=True, color=INDIGO)
quote_box(
    "\u201cThe founder needs to click the photos from every school. For that purpose he "
    "has to take a bag and a large camera. The need is that the camera has a feature that "
    "names photos with a forwarding number as the image name.\u201d"
)
para("Solution Designed", bold=True, color=INDIGO)
para(
    "An Android companion app was developed that captures a photo, saves it directly into "
    "a specified folder, and renames it with a DSLR-style sequential serial number "
    "(IMG_0001, IMG_0002, and so on). The naming is derived from the last number in the "
    "folder, so the sequence continues correctly across sessions."
)
para("Outcome", bold=True, color=INDIGO)
para(
    "The app was installed on the founder\u2019s phone during the visit. Ten photographs "
    "were captured in sequence and verified to have the correct filenames in the correct "
    "folder."
)
add_photo("record_02.jpg",
          "Figure 4.2 \u2014 Field visit to Baba ID Cards Solutions, Shelar.")
ornament()


# -------------------- RECORD 03 --------------------
bar_heading("4.2.3  Record 03 \u2014 V Tech ID Solutions, Kariwali", color=RUST)
info_table([
    ("Startup Name", "V Tech ID Solutions"),
    ("Founder", "Venkatesh Chitiken"),
    ("Village", "Kariwali"),
    ("Date of Visit", "24 September 2026"),
    ("Time of Visit", "02:59 PM"),
])
para("Background of the Enterprise", bold=True, color=INDIGO)
para(
    "V Tech ID Solutions is a small ID-card service business based in Kariwali. The "
    "founder processes photographs submitted by schools, colleges, and offices for ID "
    "cards and other official documents. A typical week involves processing between 200 "
    "and 500 photographs."
)
para("Observed Friction Point", bold=True, color=INDIGO)
para(
    "The core workflow was background replacement \u2014 taking each submitted photo and "
    "replacing its background with a clean, standard colour before printing. The founder "
    "was doing this manually: upload, wait, select, download, and repeat for every single "
    "image."
)
para("Founder\u2019s Own Statement", bold=True, color=INDIGO)
quote_box(
    "\u201cFacing problem in manually selecting every photo \u2014 upload, change "
    "background, download, then repeat. This has to be done for each photo individually.\u201d"
)
para("Solution Designed", bold=True, color=INDIGO)
para(
    "A bulk background removal tool was built using the withoutbg model. The tool takes "
    "a folder of input images, removes the background from each one in a single pass, and "
    "saves the cleaned results into an output folder with the original filenames intact."
)
para("Outcome", bold=True, color=INDIGO)
para(
    "The tool was tested on a batch of 30 photographs during the visit. The batch completed "
    "in under two minutes, compared to the founder\u2019s estimate of roughly ninety minutes "
    "manually."
)
add_photo("record_03.jpg",
          "Figure 4.3 \u2014 Field visit to V Tech ID Solutions, Kariwali.")
ornament()


# -------------------- RECORD 04 --------------------
bar_heading("4.2.4  Record 04 \u2014 Digital ID Solutions, Khoni Gaon", color=RUST)
info_table([
    ("Startup Name", "Digital ID Solutions"),
    ("Founder", "Santosh Chitiken"),
    ("Village", "Khoni Gaon"),
    ("Date of Visit", "24 September 2026"),
    ("Time of Visit", "05:04 PM"),
])
para("Background of the Enterprise", bold=True, color=INDIGO)
para(
    "Digital ID Solutions is based in Khoni Gaon and provides ID-card and school "
    "photography services. The founder handles the full pipeline from photographing "
    "students to producing finished ID cards. The business operates on a batch model \u2014 "
    "each school visit produces a large set of photographs that must be processed into a "
    "consistent ID-card format."
)
para("Observed Friction Point", bold=True, color=INDIGO)
para(
    "The bottleneck was the cropping step. After every school photo shoot, the founder "
    "had to open each photograph in an editor, adjust the crop window to frame the face "
    "and shoulders correctly, and save. On a recent shoot, the founder had clicked 500 "
    "photographs of students at a single school, each requiring manual crop adjustment."
)
para("Founder\u2019s Own Statement", bold=True, color=INDIGO)
quote_box(
    "\u201cThe founder clicked 500 photos of students at a school and then had to crop "
    "the entire batch manually by adjusting the zoom and shoulder position for each "
    "individual photo.\u201d"
)
para("Solution Designed", bold=True, color=INDIGO)
para(
    "An auto-crop web application was built using RetinaFace for face detection and "
    "Pillow for image manipulation. The tool accepts a batch of photographs, detects "
    "every face, infers the shoulder line, and crops each photograph to a standard "
    "ID-card ratio with the face and shoulders correctly positioned."
)
para("Outcome", bold=True, color=INDIGO)
para(
    "The tool was demonstrated on a set of test photographs during the visit. A batch of "
    "50 photos was processed in approximately thirty seconds, with consistently framed "
    "results. For a 500-photo shoot, the tool reduces the processing time from a full "
    "day to a few minutes."
)
add_photo("record_04.jpg",
          "Figure 4.4 \u2014 Field visit to Digital ID Solutions, Khoni Gaon.")
ornament()


# -------------------- SUMMARY TABLE --------------------
bar_heading("Summary of Field Visits")
tbl = doc.add_table(rows=1, cols=5); tbl.autofit = True
hdr = tbl.rows[0].cells
for i, h in enumerate(["Startup", "Founder", "Village", "Date", "Time"]):
    hdr[i].text = h
    hdr[i].paragraphs[0].runs[0].bold = True
    hdr[i].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string("FFFFFF")
    shade_cell(hdr[i], INDIGO)
    border_cell(hdr[i], "all", color=INDIGO, sz=10)
for r in [
    ("Srividyaniketan Classes", "Niraj", "Bhiwandi", "03-Oct-2026", "11:20 AM"),
    ("Baba ID Cards Solutions", "Shridhar Siripuram", "Shelar", "29-Sep-2026", "01:14 PM"),
    ("V Tech ID Solutions", "Venkatesh Chitiken", "Kariwali", "24-Sep-2026", "02:59 PM"),
    ("Digital ID Solutions", "Santosh Chitiken", "Khoni Gaon", "24-Sep-2026", "05:04 PM"),
]:
    row = tbl.add_row().cells
    for i, v in enumerate(r):
        row[i].text = v
        border_cell(row[i], "all", color=INDIGO, sz=6)
doc.add_paragraph()


# -------------------- CROSS-CUTTING --------------------
bar_heading("4.3  Cross-Cutting Observations")
para(
    "Looking across the four visits, several patterns emerge that are worth recording "
    "explicitly. These patterns are not visible in any single record but become clear "
    "when the four are considered together."
)
for title, body in [
    ("Pattern 1 \u2014 The problem is known; the tool is missing",
     "In every visit, the founder already understood the general category of the problem "
     "they were facing. They did not need to be convinced of the value of digitisation. "
     "What they lacked was a specific tool that fit their exact workflow, or the technical "
     "know-how to set up a generic tool."),
    ("Pattern 2 \u2014 Repetitive manual work is the primary bottleneck",
     "Three of the four enterprises had the same underlying problem: repetitive manual "
     "processing of a large volume of photographs. When shown the automated version, each "
     "founder immediately recognised the value."),
    ("Pattern 3 \u2014 The photo-services cluster is an emerging local market",
     "Three of the four enterprises visited operate in what can be described as the ID-card "
     "and school-photography market. The Bhiwandi region has a dense cluster of schools and "
     "colleges, and demand for ID-card services is high."),
    ("Pattern 4 \u2014 Fit beats sophistication",
     "In every case, the solution that was adopted was the one that required the least "
     "change to the founder\u2019s existing workflow. Fit over features should guide future "
     "interventions."),
    ("Pattern 5 \u2014 Follow-up is not optional",
     "Even the most promising demonstrations were followed by questions from the founders "
     "about edge cases and long-term data safety. Without a follow-up, some of these "
     "questions would have gone unanswered."),
]:
    p = doc.add_paragraph()
    r = p.add_run(title); r.bold = True; r.font.color.rgb = RGBColor.from_string(RUST)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    para(body)


# -------------------- PRODUCT DEMOS --------------------
bar_heading("4.4  Product Demos \u2014 Software Tools Developed")
para(
    "During the field work, three recurring friction points emerged that could not be "
    "solved by training alone. In response, three small software utilities were developed "
    "that directly address these problems. Each tool is demonstrated on the project "
    "website at https://cep-project-python.onrender.com/demos, with embedded video "
    "walkthroughs."
)

para("Demo 1: Auto Face & Shoulder Cropping Web App", bold=True, color=INDIGO)
para(
    "Developed in response to Record 04 (Digital ID Solutions). The tool accepts a batch "
    "of photographs, detects every face using RetinaFace, infers the shoulder line, and "
    "crops each photo to standard ID or portrait ratios. It handles both single uploads "
    "and batch processing, and saves output with the original filenames so the founder\u2019s "
    "existing folder structure is preserved."
)
para("Technology stack: Python, RetinaFace, Pillow, Flask.", italic=True)

para("Demo 2: Bulk Background Removal Utility", bold=True, color=INDIGO)
para(
    "Developed in response to Record 03 (V Tech ID Solutions). The tool processes an "
    "entire folder of product or ID photographs in a single run, removing the background "
    "from each image and saving the cleaned output with a clean white or transparent "
    "backdrop. It uses the withoutbg model, which runs locally without needing an "
    "internet connection."
)
para("Technology stack: Python, withoutbg, Pillow.", italic=True)

para("Demo 3: Smart Camera Renamer (Android App)", bold=True, color=INDIGO)
para(
    "Developed in response to Record 02 (Baba ID Cards Solutions). The Android app "
    "captures a photo, saves it directly into a specified target folder, and renames it "
    "with a DSLR-style sequential serial number (IMG_0001, IMG_0002, and so on). The "
    "naming sequence continues across sessions, so a founder can return to a school a "
    "week later and pick up where the last batch ended."
)
para("Technology stack: Android, Kotlin, EXIF metadata.", italic=True)


# -------------------- WEBSITE --------------------
bar_heading("4.5  Project Website \u2014 Deployment and Features")
para(
    "To make the project\u2019s findings, training materials, and software tools "
    "accessible beyond the immediate team, a web application was built and deployed "
    "using Flask, MySQL, and Jinja2 templates styled with Tailwind CSS. The application "
    "is live at:"
)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("https://cep-project-python.onrender.com")
r.bold = True; r.font.size = Pt(13)

para("Architecture", bold=True, color=INDIGO)
arch = doc.add_table(rows=1, cols=3); arch.autofit = True
for i, h in enumerate(["Component", "Technology", "Purpose"]):
    arch.rows[0].cells[i].text = h
    arch.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    arch.rows[0].cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string("FFFFFF")
    shade_cell(arch.rows[0].cells[i], INDIGO)
    border_cell(arch.rows[0].cells[i], "all", color=INDIGO, sz=10)
for comp, tech, purpose in [
    ("Backend framework", "Flask 3.0", "Routing, request handling, template rendering"),
    ("ORM", "Flask-SQLAlchemy", "Database modelling and queries"),
    ("Database", "MySQL (Aiven-hosted)", "Persistent storage for field visit records"),
    ("Frontend", "Jinja2 + Tailwind CSS", "Responsive server-rendered pages"),
    ("Photo storage", "Cloudinary", "Persistent CDN-hosted uploads"),
    ("Deployment", "Render + Gunicorn", "WSGI-served production deployment"),
]:
    row = arch.add_row().cells
    row[0].text, row[1].text, row[2].text = comp, tech, purpose
    for c in row:
        border_cell(c, "all", color=INDIGO, sz=6)
doc.add_paragraph()

para("Routes", bold=True, color=INDIGO)
rt = doc.add_table(rows=1, cols=3); rt.autofit = True
for i, h in enumerate(["Route", "Method", "Description"]):
    rt.rows[0].cells[i].text = h
    rt.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    rt.rows[0].cells[i].paragraphs[0].runs[0].font.color.rgb = RGBColor.from_string("FFFFFF")
    shade_cell(rt.rows[0].cells[i], INDIGO)
    border_cell(rt.rows[0].cells[i], "all", color=INDIGO, sz=10)
for route, method, desc in [
    ("/", "GET", "Project overview, objectives, team, methodology"),
    ("/dashboard", "GET", "Metrics and full data table of every field visit"),
    ("/field-work", "GET, POST", "Card grid of visits; POST adds a new record with photo upload"),
    ("/resources", "GET", "Intervention areas with downloadable training materials"),
    ("/demos", "GET", "Embedded video demos of the three software tools"),
]:
    row = rt.add_row().cells
    row[0].text, row[1].text, row[2].text = route, method, desc
    for c in row:
        border_cell(c, "all", color=INDIGO, sz=6)
doc.add_paragraph()

para(
    "The dashboard displays three metrics \u2014 Places Visited, Enterprises Supported, "
    "and Region \u2014 followed by a full table of field visit records. The field work "
    "page presents each visit as a stamp card styled after a field notebook, with "
    "enterprise photos, date stamps, before/after status pills, and founder statements. "
    "The resources page lists the four intervention areas with downloadable training "
    "materials. The demos page embeds video walkthroughs of the three software tools."
)
page_break()


# ##################################################################
# #                     CHAPTER 5                                  #
# ##################################################################
section_title("CHAPTER 5  \u2014  CONCLUSION AND RECOMMENDATIONS")

bar_heading("5.1  Conclusion")
para(
    "The Technical Support for Rural Startups project demonstrated that direct, "
    "hands-on technical support, combined with purpose-built software tools and a "
    "public-facing record of outcomes, is an effective approach for promoting digital "
    "adoption among rural micro-enterprises. Unlike one-off workshops or pamphlets, "
    "working alongside each entrepreneur \u2014 setting up tools, building catalogues, "
    "and solving specific problems together \u2014 produced measurable adoption."
)
para(
    "The project also showed that training alone is not sufficient. Follow-up visits "
    "were essential to sustain new habits, and the three software tools developed "
    "during the project addressed specific friction points that training could not "
    "solve. The project website serves as both a record of the field work and a "
    "reusable resource for future CEP cohorts."
)
para(
    "Across the four enterprises visited, the most consistent lesson was that the "
    "founders already knew what they needed. They were not waiting to be told that "
    "digitisation is important. They were waiting for someone to sit with them, on "
    "their own device, and help them get the tool working. That is the specific "
    "contribution a CEP field visit can make."
)

bar_heading("5.2  Key Findings")
bullets([
    "Hands-on support overcomes hesitation: Entrepreneurs who had never used digital "
    "tools adopted them when the setup was done with them, not for them.",
    "Follow-up is essential: Habits introduced on day one rarely survived the week "
    "without a second check-in.",
    "Fit beats sophistication: Tools and workflows that matched existing record-keeping "
    "habits were adopted faster than those that replaced them.",
    "Purpose-built tools fill gaps: The auto crop, background removal, and camera "
    "renamer utilities addressed problems that training alone could not.",
    "Documentation matters: Storing visit records in a structured database and "
    "publishing them on a website created a reusable record that outlasts any single "
    "field visit.",
    "A recurring local cluster: Three of four enterprises faced the same photo-processing "
    "bottleneck, suggesting a larger market for these tools.",
])

bar_heading("5.3  Significance of Findings")
para(
    "The findings confirm that rural digital adoption is not primarily a knowledge "
    "problem \u2014 it is a support and fit problem. Most entrepreneurs understand why "
    "digital tools are useful; what they need is someone to sit with them and set "
    "things up, plus simple tools that work within their existing habits. Colleges "
    "and universities running CEP programs are well-positioned to provide this kind "
    "of sustained, hands-on support."
)

bar_heading("5.4  Recommendation")
bullets([
    "Continue the three-visit model: Needs assessment, hands-on onboarding, and "
    "follow-up review. Do not skip the follow-up.",
    "Build for fit, not features: Tool development should start from observed friction "
    "points, not from assumptions about what entrepreneurs need.",
    "Document everything: Maintain structured records of every visit, including founder "
    "statements and before/after status.",
    "Publish outcomes: Deploy the project website publicly so that future cohorts can "
    "build on existing work.",
    "Train on real accounts: Set up tools on the entrepreneur\u2019s actual device, "
    "not a demo device.",
    "Look for clusters: When multiple enterprises face the same problem, that is a "
    "signal to build a reusable tool rather than resolve each case individually.",
])

bar_heading("5.5  Final Remark")
para(
    "The Technical Support for Rural Startups project at B.N.N. College, Bhiwandi, "
    "has shown that meaningful digital adoption in rural areas is achievable when "
    "support is direct, patient, and matched to the entrepreneur\u2019s actual habits. "
    "The field visits, the software tools, and the deployed website together form a "
    "complete record of what was done \u2014 and a foundation for what can be done next."
)
page_break()


# ##################################################################
# #                     REFERENCES                                 #
# ##################################################################
section_title("REFERENCES")
for r in [
    "Ministry of Electronics and Information Technology, Government of India. "
    "(2023). Digital Personal Data Protection Act, 2023.",
    "Reserve Bank of India. (2024). UPI Transaction Statistics.",
    "Google. (2025). Google Business Profile \u2014 Official Documentation.",
    "WhatsApp Business. (2025). WhatsApp Business Catalogue \u2014 Product Guide.",
    "Telecom Regulatory Authority of India. (2024). Annual Report on Internet "
    "Penetration in Rural India.",
    "NASSCOM. (2023). Digital Adoption in Indian Micro-Enterprises.",
    "Field Interaction Notes and Photographs, Villages near Bhiwandi, Maharashtra.",
    "Project Website: https://cep-project-python.onrender.com",
]:
    p = doc.add_paragraph(r, style="List Bullet")
    p.paragraph_format.line_spacing = 1.4

section_title("APPENDICES")
for a in [
    "Appendix A: Field Visit Form (structure and fields)",
    "Appendix B: Photos of Field Interaction (Chapter 4, Figures 4.1\u20134.4)",
    "Appendix C: Inventory Management Template (Automated_Inventory_Management.xlsx)",
    "Appendix D: UPI Setup & First Payment Guide (upi_setup.pptx)",
    "Appendix E: Online Discoverability Guide (Online_Discover.pptx)",
    "Appendix F: Product Demo Videos (available at /demos)",
]:
    p = doc.add_paragraph(a, style="List Bullet")
    p.paragraph_format.line_spacing = 1.4


# ##################################################################
# #           FORMAL PAGE BORDER + PAGE NUMBERS                    #
# ##################################################################
for sec in doc.sections:
    add_page_border(sec, style="thinThickSmallGap", sz="12", space="24", color=INDIGO)
    add_page_numbers(sec)


# ##################################################################
# #                     SAVE                                       #
# ##################################################################
doc.save(OUT)
print(f"\n[OK] Report written to:\n     {OUT}\n")
print("Open it in Word, then:")
print("  • Insert → Table of Contents  (replaces the plain-text placeholder)")
print("  • File → Save As → PDF  (if your college needs PDF submission)")