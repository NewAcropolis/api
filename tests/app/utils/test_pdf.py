import base64
import os

from app.utils.pdf import extract_topics


class WhenExtractingTopics:

    def it_extracts_all_topics_from_pdf(self):
        with open(os.path.join('tests', 'test_files', 'test_magazine.pdf'), "rb") as f:
            pdf_data = f.read()

        topics = extract_topics(pdf_data)

        assert str(topics) == 'Philosophy: Something About Philosophy\n' \
            'Culture: Something About Culture And Another Heading Final Heading'
