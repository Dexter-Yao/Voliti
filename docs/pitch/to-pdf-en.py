"""
Convert mentor-showcase-en.html to PDF via Chrome headless.
"""
import os
import re
import subprocess
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
HTML_IN = os.path.join(DIR, "mentor-showcase-en.html")
HTML_PRINT = os.path.join(DIR, "print-ready-en.html")
PDF_OUT = os.path.join(DIR, "Voliti-Product-Showcase.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

with open(HTML_IN, "r") as f:
    html = f.read()

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

  .page-wrapper {
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
  }

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

  .section-title {
    font-size: 28px !important;
    margin-bottom: 12px !important;
    line-height: 1.25 !important;
  }

  .section-label { margin-bottom: 8px !important; }

  .section-desc {
    font-size: 14px !important;
    line-height: 1.6 !important;
    max-width: 1100px !important;
  }

  .section-desc + .section-desc { margin-top: 8px !important; }

  .stat-grid { gap: 20px !important; margin: 20px 0 !important; }
  .stat-number { font-size: 28px !important; margin-bottom: 4px !important; }
  .stat-label { font-size: 12px !important; line-height: 1.5 !important; }
  .stat-card { padding: 14px !important; }

  .feature-grid { gap: 16px !important; margin: 20px 0 !important; }
  .feature-card { padding: 16px !important; }
  .feature-card-title { font-size: 16px !important; margin-bottom: 4px !important; }
  .feature-card-desc { font-size: 12px !important; line-height: 1.5 !important; }
  .feature-card-num { margin-bottom: 4px !important; }

  .quote-block { padding: 10px 16px !important; margin: 12px 0 !important; }
  .quote-text { font-size: 15px !important; line-height: 1.5 !important; }
  .quote-attr { margin-top: 4px !important; }

  .flex-row {
    display: flex !important;
    flex-direction: row !important;
    gap: 32px !important;
    align-items: flex-start !important;
    max-height: 520px !important;
  }

  .phone-frame {
    transform: scale(0.55) !important;
    transform-origin: top center !important;
    box-shadow: none !important;
    border: 1px solid rgba(26, 24, 22, 0.15) !important;
    margin-bottom: -306px !important;
    flex-shrink: 0 !important;
    width: 375px !important;
  }

  .flex-col-text {
    flex: 1 !important;
    min-width: 0 !important;
    max-width: 700px !important;
  }

  .scenario-note {
    padding: 8px 12px !important;
    margin: 8px 0 !important;
    font-size: 12px !important;
    line-height: 1.5 !important;
  }

  .section-desc[style] { margin-bottom: 16px !important; }

  .witness-card-frame {
    transform: scale(0.7) !important;
    transform-origin: top center !important;
    margin-bottom: -60px !important;
    flex-shrink: 0 !important;
  }

  .positioning-chart {
    width: 700px !important;
    height: 380px !important;
    margin: 12px auto !important;
  }

  .arch-diagram {
    margin: 16px auto !important;
    gap: 14px !important;
    max-width: 1100px !important;
    width: 100% !important;
  }

  .arch-box { padding: 10px !important; }
  .arch-box-title { font-size: 13px !important; }
  .arch-box-desc { font-size: 11px !important; line-height: 1.4 !important; }
  .arch-label { font-size: 10px !important; width: 80px !important; padding: 8px 8px 8px 0 !important; }
  .arch-arrow { font-size: 14px !important; padding-left: 80px !important; }

  .thankyou.page-section {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
  }

  .thankyou-text { font-size: 36px !important; }
"""

html = html.replace("</style>", pdf_css + "\n</style>")

with open(HTML_PRINT, "w") as f:
    f.write(html)

print(f"Print-ready HTML: {HTML_PRINT}")

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

os.remove(HTML_PRINT)
print("Done.")
