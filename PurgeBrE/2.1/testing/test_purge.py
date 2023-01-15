import unittest

from bs4 import BeautifulSoup

from purge_bre.AddonInitializer import remove_bre_in_longman5_mdx


class PurgeTestCase(unittest.TestCase):
    def test_remove_bre_in_longman5_mdx(self):
        soup = BeautifulSoup("<html><body><span class=\"golden-dict-media-word-sound\"> [sound:p008-001718624.mp3]</span><span class=\"golden-dict-media-word-sound\"> [sound:p008-test.mp3]</span></body></html>", 'html.parser')
        remove_bre_in_longman5_mdx(soup)
        html = str(soup)
        self.assertEqual(html, "<html><body><span class=\"golden-dict-media-word-sound\"> [sound:p008-test.mp3]</span></body></html>")


if __name__ == '__main__':
    unittest.main()
