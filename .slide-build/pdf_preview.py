from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader
import pypdfium2 as pdfium

root = Path(__file__).resolve().parent.parent
out = root / 'deliverables/Rack_Manifold_Optimization_MEAM5020_Preview.pdf'
c = Canvas(str(out), pagesize=(720,405))
c.setTitle('MEAM 5020: Rack Manifold Optimization')
c.setAuthor('Constantin de Lint, David Kim, Jason Simon, Sam Vasington')
urls = [
 'https://scispace.com/pdf/numerical-and-experimental-investigations-of-patterned-flow-6skn0d5dfr.pdf',
 'https://doi.org/10.1155/2014/325259',
 'https://doi.org/10.1016/j.expthermflusci.2016.02.004',
 'https://docs.nvidia.com/dgx/dgxgb200-user-guide/hardware.html',
 'https://coolprop.org/fluid_properties/Incompressibles.html',
 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html',
 'https://github.com/jasonsimon999/NVL72-Manifold-Optimization',
]
for i in range(1,16):
 c.drawImage(str(root / f'.slide-build/final-render/slide-{i}.png'),0,0,width=720,height=405)
 if i == 15:
  top=108
  for url,height in zip(urls,[52,52,72,31,31,31,55]):
   c.linkURL(url,(34,405-(top+height)*.75,688,405-top*.75),relative=0,thickness=0)
   top+=height+3
 c.showPage()
c.save()
assert len(PdfReader(out).pages) == 15
doc=pdfium.PdfDocument(str(out))
for i,page in enumerate(doc):
 page.render(scale=1.333333).to_pil().save(root / f'.slide-build/pdf-check-{i+1}.png')
print(out)
