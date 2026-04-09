"""
Convert mentor-showcase.html to PDF via Chrome headless.
Injects comprehensive print CSS to adapt the scrolling web page
into fixed 1440x810 landscape slides.
"""
import os
import re
import subprocess
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
HTML_IN = os.path.join(DIR, "mentor-showcase.html")
HTML_PRINT = os.path.join(DIR, "print-ready.html")
PDF_OUT = os.path.join(DIR, "Voliti-Mentor-Showcase.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

with open(HTML_IN, "r") as f:
    html = f.read()

# Replace the ENTIRE existing @media print block + add @page rules
# First, remove the existing @media print block
html = re.sub(
    r'@media print \{[^}]*(?:\{[^}]*\}[^}]*)*\}',
    '/* original @media print removed for PDF export */',
    html
)

# Inject comprehensive PDF slide CSS before </style>
pdf_css = """
  /* ================================================
     PDF EXPORT: Convert scrolling page to 1440x810 slides
     ================================================ */
  @page {
    size: 1440px 810px;
    margin: 0;
  }

  html, body {
    margin: 0 !important;
    padding: 0 !important;
    background: var(--page-bg) !important;
    overflow: visible !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* Page wrapper: expand to fill 1440px slide width */
  .page-wrapper {
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  /* Each section = one 1440x810 slide */
  .page-section {
    width: 1440px !important;
    height: 810px !important;
    max-height: 810px !important;
    overflow: hidden !important;
    padding: 56px 80px 48px !important;
    margin: 0 !important;
    border-bottom: none !important;
    page-break-after: always !important;
    page-break-inside: avoid !important;
    box-sizing: border-box !important;
    position: relative !important;
  }

  .page-section:last-of-type {
    page-break-after: auto !important;
  }

  /* ---- COVER: center everything ---- */
  .cover.page-section {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
    padding: 80px 120px !important;
  }

  .cover .cover-brand { margin-bottom: 24px !important; }
  .cover .cover-title {
    font-size: 52px !important;
    max-width: 900px !important;
    margin-bottom: 20px !important;
  }
  .cover .cover-tagline {
    max-width: 700px !important;
    margin-bottom: 24px !important;
  }
  .cover .cover-subtitle {
    max-width: 700px !important;
    margin-bottom: 36px !important;
    font-size: 16px !important;
  }

  /* ---- Section titles: slightly smaller to save vertical space ---- */
  .section-title {
    font-size: 28px !important;
    margin-bottom: 12px !important;
    line-height: 1.25 !important;
  }

  .section-label {
    margin-bottom: 8px !important;
  }

  .section-desc {
    font-size: 14px !important;
    line-height: 1.6 !important;
    max-width: 1100px !important;
  }

  .section-desc + .section-desc {
    margin-top: 8px !important;
  }

  /* ---- Stat grid: compact ---- */
  .stat-grid {
    gap: 20px !important;
    margin: 20px 0 !important;
  }

  .stat-number {
    font-size: 28px !important;
    margin-bottom: 4px !important;
  }

  .stat-label {
    font-size: 12px !important;
    line-height: 1.5 !important;
  }

  .stat-card {
    padding: 14px !important;
  }

  /* ---- Feature grid: compact ---- */
  .feature-grid {
    gap: 16px !important;
    margin: 20px 0 !important;
  }

  .feature-card {
    padding: 16px !important;
  }

  .feature-card-title {
    font-size: 16px !important;
    margin-bottom: 4px !important;
  }

  .feature-card-desc {
    font-size: 12px !important;
    line-height: 1.5 !important;
  }

  .feature-card-num {
    margin-bottom: 4px !important;
  }

  /* ---- Quote blocks: compact ---- */
  .quote-block {
    padding: 10px 16px !important;
    margin: 12px 0 !important;
  }

  .quote-text {
    font-size: 15px !important;
    line-height: 1.5 !important;
  }

  .quote-attr {
    margin-top: 4px !important;
  }

  /* ---- Flex row (text + phone): side by side, fit in 810px ---- */
  .flex-row {
    display: flex !important;
    flex-direction: row !important;
    gap: 32px !important;
    align-items: flex-start !important;
    height: auto !important;
    max-height: 520px !important;
  }

  /* ---- Phone frames: scale uniformly to fit slide height ---- */
  .phone-frame {
    transform: scale(0.55) !important;
    transform-origin: top center !important;
    box-shadow: none !important;
    border: 1px solid rgba(26, 24, 22, 0.15) !important;
    /* Compensate for the scaled-down empty space below */
    margin-bottom: -306px !important;
    flex-shrink: 0 !important;
    /* Reserve the visual width after scaling: 375 * 0.55 ≈ 206px */
    width: 375px !important;
  }

  .flex-col-text {
    flex: 1 !important;
    min-width: 0 !important;
    max-width: 700px !important;
  }

  /* ---- Scenario notes: compact ---- */
  .scenario-note {
    padding: 8px 12px !important;
    margin: 8px 0 !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
  }

  /* Inline style margin-bottom override for flex-row sections */
  .section-desc[style] {
    margin-bottom: 16px !important;
  }

  /* ---- Witness card: scale to fit ---- */
  .witness-card-frame {
    transform: scale(0.7) !important;
    transform-origin: top center !important;
    margin-bottom: -60px !important;
    flex-shrink: 0 !important;
  }

  /* ---- Positioning chart: center in slide, proper size ---- */
  .positioning-chart {
    width: 700px !important;
    height: 380px !important;
    margin: 12px auto !important;
  }

  /* ---- Architecture diagram: center and widen ---- */
  .arch-diagram {
    margin: 16px auto !important;
    gap: 14px !important;
    max-width: 1100px !important;
    width: 100% !important;
  }

  .arch-box {
    padding: 10px !important;
  }

  .arch-box-title {
    font-size: 13px !important;
  }

  .arch-box-desc {
    font-size: 11px !important;
    line-height: 1.4 !important;
  }

  .arch-label {
    font-size: 10px !important;
    width: 80px !important;
    padding: 8px 8px 8px 0 !important;
  }

  .arch-arrow {
    font-size: 14px !important;
    padding-left: 80px !important;
  }

  /* ---- User persona cards (section 08): compact ---- */
  .feature-grid {
    grid-template-columns: 1fr 1fr !important;
  }

  /* ---- Thank you slide: center ---- */
  .thankyou.page-section {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
  }

  .thankyou-text {
    font-size: 36px !important;
  }

  /* ---- Summary section (last content section): compact ---- */
  .summary-pillars {
    gap: 32px !important;
  }
"""

html = html.replace("</style>", pdf_css + "\n</style>")

# Write print-ready HTML
with open(HTML_PRINT, "w") as f:
    f.write(html)

print(f"Print-ready HTML: {HTML_PRINT}")

# Export PDF via Chrome headless
cmd = [
    CHROME,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-software-rasterizer",
    f"--print-to-pdf={PDF_OUT}",
    "--no-pdf-header-footer",
    f"file://{HTML_PRINT}",
]

print("Running Chrome headless...")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

if result.returncode == 0 and os.path.exists(PDF_OUT):
    size_mb = os.path.getsize(PDF_OUT) / (1024 * 1024)
    print(f"PDF saved: {PDF_OUT} ({size_mb:.1f} MB)")
else:
    print(f"Chrome stderr: {result.stderr}")
    print(f"Chrome stdout: {result.stdout}")
    sys.exit(1)

# Cleanup
os.remove(HTML_PRINT)
print("Done.")
