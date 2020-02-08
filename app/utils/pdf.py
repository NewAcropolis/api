import pdftotext
from PIL import Image
from wand.image import Image
import os
import io

TOPICS = [
    'Philosophy',
    'Society',
    'Esoterica',
    'Art',
    'Culture',
    'Science & Nature',
    'Gods & Heroes',
    'Myths Of The World'
]


def extract_first_page(blob):
    pdf = Image(blob=blob, resolution=200)

    image = Image(
        width=pdf.width,
        height=pdf.height
    )

    image.composite(
        pdf.sequence[0],
        top=0,
        left=0
    )

    return image.make_blob('png')


def extract_topics(pdf_binary):
    pdf = pdftotext.PDF(io.BytesIO(pdf_binary))

    topic_headings = ''

    for n in range(4, len(pdf)):
        topic = ''
        topic_heading = ''
        for line_no, l in enumerate(pdf[n].split('\n')):
            words = [w.capitalize() for w in l.strip().split(' ') if w.strip()]

            if not words:
                continue

            if not topic and len(words) < 5:
                heading = ' '.join(words)
                if heading in TOPICS:
                    topic = heading
                    continue

            if topic:
                line = ' '.join(words)
                if len(line) < 30 and u'\u201c' not in line:
                    topic_heading += line + ' '

            if line_no > 2:
                break

        if topic_heading:
            topic_headings += '{}: {}\n'.format(topic, topic_heading[:-1])

    return topic_headings[:-1] if topic_headings else ''
