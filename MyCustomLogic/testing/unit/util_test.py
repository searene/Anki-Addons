import re
import unittest

from my_custom_logic.common.util import split


class SplitTestCase(unittest.TestCase):
    def test_case1(self):
        text = "stagger1 /ˈstæɡə $ -ər/[sound:stagger1.mp3] ●●○ verb [sound:stagger_n0205.mp3] [sound:stagger1.mp3]"
        expected_output = ("stagger", "/ˈstæɡə $ -ər/", "[sound:stagger1.mp3]", "verb")
        self.assertEqual(expected_output, split(text))

    def test_case2(self):
        text = "antics /ˈæntɪks/[sound:antics.mp3] noun [plural] [sound:brelasdeantics.mp3] [sound:antics.mp3]"
        expected_output = ("antics", "/ˈæntɪks/", "[sound:antics.mp3]", "noun [plural]")
        self.assertEqual(expected_output, split(text))

    def test_split_no_match(self):
        text = "no match here"
        expected_output = ("no match here", "", "", "")
        self.assertEqual(expected_output, split(text))


if __name__ == '__main__':
    unittest.main()