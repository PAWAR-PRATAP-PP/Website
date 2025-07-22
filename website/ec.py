from fpdf import FPDF

class MarkingPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "PhD Entrance Exam Marking System", ln=True, align="C")
        self.ln(5)

    def section_title(self, title):
        self.set_font("Arial", "B", 11)
        self.set_text_color(0)
        self.multi_cell(0, 8, title)
        self.ln(1)

    def section_body(self, body):
        self.set_font("Arial", "", 10)
        # Replace problematic Unicode characters
        safe_text = body.replace("–", "-").replace("’", "'")
        self.multi_cell(0, 8, safe_text)
        self.ln(2)

pdf = MarkingPDF()
pdf.add_page()

marking_sections = [
    ("1. UGC-NET (Computer Science - Paper II)", """
Paper I (General Aptitude):
- 50 questions, 2 marks each = 100 marks
- No negative marking

Paper II (Subject - Computer Science):
- 100 questions, 2 marks each = 200 marks
- No negative marking

Each paper is 100 minutes.
"""),
    ("2. GATE (CSE) - For PhD in IITs, NITs, IISc", """
- Total: 65 questions, 100 marks
- General Aptitude: 10 questions = 15 marks
- Core Subject: 55 questions = 85 marks

Negative Marking:
- 1-mark question: -0.33
- 2-mark question: -0.66

Question types: MCQs, MSQs, NAT
"""),
    ("3. University-Level PhD Entrance Exams (DU, BHU, VIT, etc.)", """
Typical Structure:
- Research Aptitude: 20-30 questions = 20-30 marks
- Subject Knowledge: 50-70 questions = 70-100 marks
- Interview: Usually 30-50 marks

Cutoff: Usually 50% for general, 45% for reserved categories
Weightage: Written Exam (70%) + Interview (30%)
"""),
    ("4. Private University PhD Exams (Amity, SRM, etc.)", """
- Written Test: 70-100 marks
- Topics: Research Methods, Core CS, Logical Reasoning
- Interview: Often mandatory
- Some accept UGC-NET/GATE scores directly
"""),
    ("Common Features Across Most Exams", """
- Format: MCQs (sometimes subjective/interview)
- Negative marking in some exams (especially GATE)
- Minimum Qualifying Marks: ~50% general, 45% reserved
- Interview to assess research potential and proposal
""")
]

for title, body in marking_sections:
    pdf.section_title(title)
    pdf.section_body(body)

pdf.output("PhD_Entrance_Exam_Marking_System.pdf")
