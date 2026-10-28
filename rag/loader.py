from pypdf import PdfReader
import os


def load_document(path):

    reader = PdfReader(path)

    pages = []

    for page_number, page in enumerate(reader.pages):

        text = page.extract_text()

        pages.append(
            {
                "text": text,
                "metadata": {
                    "source": os.path.basename(path),
                    "page": page_number + 1
                }
            }
        )


    return pages