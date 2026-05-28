"""Convert slides.html to slides.pdf using weasyprint."""
import sys
from pathlib import Path
from weasyprint import HTML

HERE = Path(__file__).parent
src = HERE / "slides.html"
out = HERE / "slides.pdf"

print(f"Reading: {src}")
HTML(filename=str(src), base_url=str(HERE)).write_pdf(str(out))
print(f"Wrote:   {out}  ({out.stat().st_size//1024} KB)")
