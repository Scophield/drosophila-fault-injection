from pathlib import Path
import sys
import unittest
import pymupdf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from qa_pdf import references_only_fifth_page


class PageLimit(unittest.TestCase):
    def test_technical_fifth_page_rejected_and_reference_only_accepted(self):
        doc=pymupdf.open()
        for _ in range(4):doc.new_page().insert_text((72,72),'Technical content')
        p=doc.new_page();p.insert_text((72,72),'Technical conclusion')
        self.assertFalse(references_only_fifth_page(doc))
        doc.delete_page(4);p=doc.new_page();p.insert_text((72,72),'REFERENCES\n[1] Primary source.')
        self.assertTrue(references_only_fifth_page(doc))
        p.draw_rect(pymupdf.Rect(72,110,150,170))
        self.assertFalse(references_only_fifth_page(doc))
        doc.new_page()
        self.assertFalse(references_only_fifth_page(doc))
        doc.close()


if __name__=='__main__': unittest.main()
