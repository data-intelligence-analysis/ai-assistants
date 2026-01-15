from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

def draw_table(c, x, y, data, col_widths=None, row_height=18, header=True):
    # data: list of lists (rows)
    if not data:
        return y
    n_cols = len(data[0])
    if col_widths is None:
        col_widths = [ (6.5*inch)/n_cols for _ in range(n_cols) ]
    # header style
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    curr_y = y
    for r, row in enumerate(data):
        if r == 0 and header:
            c.setFillColor(colors.HexColor("#f0f0f0"))
            c.rect(x, curr_y-row_height+3, sum(col_widths), row_height, fill=1, stroke=0)
            c.setFillColor(colors.black)
        else:
            c.setFont("Helvetica", 10)
        cx = x + 2
        for ci, cell in enumerate(row):
            c.drawString(cx, curr_y-row_height+6, str(cell))
            cx += col_widths[ci]
        curr_y -= row_height
    return curr_y

def income_statement_pdf_grouped(path, company, period_label, df, currency="USD"):
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height-72, f"{company} — Income Statement ({period_label})")
    c.setFont("Helvetica", 10)
    c.drawString(72, height-90, f"Currency: {currency}")
    # Build table
    header = ["Period", "Revenue", "COGS", "Gross Profit", "OpEx", "Net Income"]
    rows = [header]
    for _, r in df.iterrows():
        rows.append([
            r['period'],
            f"{r['Revenue']:.2f}",
            f"{r['COGS']:.2f}",
            f"{r['Gross Profit']:.2f}",
            f"{r['Operating Expenses']:.2f}",
            f"{r['Net Income']:.2f}",
        ])
    y = draw_table(c, 72, height-130, rows, col_widths=[1.4*inch, 0.9*inch, 0.8*inch, 1.0*inch, 0.8*inch, 0.9*inch])
    c.showPage()
    c.save()
def balance_sheet_pdf(path, company, bs, currency="USD"):
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height-72, f"{company} — Balance Sheet (As of {bs['as_of']})")
    c.setFont("Helvetica", 10)
    c.drawString(72, height-90, f"Currency: {currency}")
    # Assets
    rows = [["Assets", "Amount"]]
    for k, v in bs['assets'].items():
        rows.append([k, f"{v:.2f}"])
    rows.append(["Total Assets", f"{bs['totals']['Assets']:.2f}"])
    y = draw_table(c, 72, height-130, rows, col_widths=[2.5*inch, 1.2*inch])

    # Liabilities
    rows = [["Liabilities", "Amount"]]
    for k, v in bs['liabilities'].items():
        rows.append([k, f"{v:.2f}"])
    y -= 10
    y = draw_table(c, 72, y, rows, col_widths=[2.5*inch, 1.2*inch])

    # Equity
    rows = [["Equity", "Amount"]]
    for k, v in bs['equity'].items():
        rows.append([k, f"{v:.2f}"])
    y -= 10
    y = draw_table(c, 72, y, rows, col_widths=[2.5*inch, 1.2*inch])

    # Check
    y -= 10
    rows = [["Check", "Amount"]]
    rows.append(["Liabilities + Equity", f"{bs['totals']['Liabilities + Equity']:.2f}"])
    rows.append(["Net Income (YTD)", f"{bs['net_income_ytd']:.2f}"])
    draw_table(c, 72, y, rows, col_widths=[2.5*inch, 1.2*inch])

    c.showPage()
    c.save()

def income_statement_pdf(path, company, period_label, df, currency='USD'):
    c = canvas.Canvas(str(path), pagesize=LETTER)
    c.drawString(72, 750, f"{company} - Income Statement ({period_label})")
    y = 720
    c.drawString(72,y,'Period | Revenue | Expenses | Net Income')
    y-=20
    for _, r in df.iterrows():
        c.drawString(72,y,f"{r['period']} | {r['Revenue']:.2f} | {r['Expenses']:.2f} | {r['Net Income']:.2f}")
        y-=16
    c.showPage(); c.save()

def balance_sheet_pdf(path, company, bs, currency='USD'):
    c = canvas.Canvas(str(path), pagesize=LETTER)
    c.drawString(72,750,f"{company} - Balance Sheet (As of {bs['as_of']})")
    y = 720
    c.drawString(72,y,f"Total Assets: {bs['totals']['Assets']:.2f}")
    y-=20
    c.drawString(72,y,f"Liabilities + Equity: {bs['totals']['Liabilities + Equity']:.2f}")
    c.showPage(); c.save()
