"""Submission features are checked from reopened PDF bytes, including invisible links."""
from pathlib import Path
import sys
import unittest

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from qa_pdf import submission_errors, submission_features


class PDFSubmissionTests(unittest.TestCase):
    def make_document(self):
        doc = pymupdf.open()
        doc.new_page().insert_text((72, 72), 'Printable reference: https://example.org')
        return doc

    def inspect_saved(self, doc, **save_options):
        with pymupdf.open(stream=doc.tobytes(**save_options), filetype='pdf') as saved:
            return submission_features(saved)

    def test_printable_url_has_no_interactive_features(self):
        with self.make_document() as doc:
            self.assertEqual(submission_errors(self.inspect_saved(doc)), [])

    def test_hidden_link_and_outline_are_rejected(self):
        with self.make_document() as doc:
            doc[0].insert_link({'kind': pymupdf.LINK_URI,
                                'from': pymupdf.Rect(72, 60, 300, 76),
                                'uri': 'https://example.org'})
            doc.set_toc([[1, 'A hidden-style bookmark', 1]])
            features = self.inspect_saved(doc)
        self.assertEqual(features['links_per_page'], [1])
        self.assertEqual(features['bookmarks'], 1)
        self.assertEqual(len(submission_errors(features)), 2)

    def test_form_is_rejected(self):
        with self.make_document() as doc:
            widget = pymupdf.Widget()
            widget.field_name = 'response'
            widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(72, 100, 250, 125)
            doc[0].add_widget(widget)
            features = self.inspect_saved(doc)
        self.assertEqual(features['widgets_per_page'], [1])
        self.assertIn('PDF contains form fields or widgets', submission_errors(features))

    def test_empty_password_encryption_is_rejected(self):
        with self.make_document() as doc:
            features = self.inspect_saved(doc, encryption=pymupdf.PDF_ENCRYPT_AES_256,
                                          owner_pw='test-owner', user_pw='')
        self.assertTrue(features['encrypted'])
        self.assertIn('PDF is encrypted', submission_errors(features))

    def test_old_pdf_version_is_rejected(self):
        with self.make_document() as doc:
            data = doc.tobytes().replace(b'%PDF-1.7', b'%PDF-1.3', 1)
        with pymupdf.open(stream=data, filetype='pdf') as saved:
            features = submission_features(saved)
        self.assertEqual(features['pdf_version'], '1.3')
        self.assertIn('PDF version is below 1.4 or unavailable', submission_errors(features))


if __name__ == '__main__':
    unittest.main()
