from typing import Optional, List
import io
import fitz
from pathlib import Path
import requests
import base64
import os
from langchain_community.document_loaders import UnstructuredPDFLoader

def query(payload):
	API_URL = "https://k05w2if7y9368qct.us-east-1.aws.endpoints.huggingface.cloud"
	API_TOKEN = os.environ.get('HF_API_KEY')
	headers = {
		"Accept" : "application/json",
		"Authorization": f"Bearer {API_TOKEN}",
		"Content-Type": "application/json" 
	}
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

def nougat(image):
    output = query({"inputs":base64.b64encode(image).decode("utf-8"), 
					"fix_markdown":True,
					"parameters": {"max_new_tokens" : 3584, 
								"return_dict_in_generate":True, 
								"output_scores":True}})
    return output['generated_text']

# def query(payload):
#     API_URL = "https://api-inference.huggingface.co/models/facebook/nougat-base"
#     API_TOKEN = os.environ.get('HF_API_KEY')
#     headers = {"Authorization": f"Bearer {API_TOKEN}"}
#     response = requests.request("POST", API_URL, headers=headers, json=payload)
#     return response.json()
# def nougat(image):
#     output = query({"inputs" : base64.b64encode(image).decode("utf-8") , 
#                     "parameters" : {"max_new_tokens" : 3584}
#                     })
#     return output['generated_text']



def rasterize_paper(
    pdf: Path,
    outpath: Optional[Path] = None,
    dpi: int = 96,
    return_pil=False,
    pages=None,
) -> Optional[List[io.BytesIO]]:
    """
    Rasterize a PDF file to PNG images.

    Args:
        pdf (Path): The path to the PDF file.
        outpath (Optional[Path], optional): The output directory. If None, the PIL images will be returned instead. Defaults to None.
        dpi (int, optional): The output DPI. Defaults to 96.
        return_pil (bool, optional): Whether to return the PIL images instead of writing them to disk. Defaults to False.
        pages (Optional[List[int]], optional): The pages to rasterize. If None, all pages will be rasterized. Defaults to None.

    Returns:
        Optional[List[io.BytesIO]]: The PIL images if `return_pil` is True, otherwise None.
    """

    pillow_images = []
    if outpath is None:
        return_pil = True
    try:
        if isinstance(pdf, (str, Path)):
            pdf = fitz.open(pdf)
        if pages is None:
            pages = range(len(pdf))
        for i in pages:
            page_bytes: bytes = pdf[i].get_pixmap(dpi=dpi).pil_tobytes(format="PNG")
            if return_pil:
                pillow_images.append(page_bytes)#(io.BytesIO(page_bytes))
            else:
                with (outpath / ("%02d.png" % (i + 1))).open("wb") as f:
                    f.write(page_bytes)
    except Exception:
        pass
    if return_pil:
        return pillow_images


def extract_markdown(filepath):
    results = []
    images = rasterize_paper(pdf=filepath, return_pil=True)
    for image in images:
        markdown = nougat(image)
        results.append(markdown)
    return results

def extract_image_table(file_path, images_path):
    loader = UnstructuredPDFLoader(file_path = file_path, 
                                extract_image_block_types=["Image", "Table"],
                                extract_image_block_to_payload=False,             
                                extract_image_block_output_dir=images_path)
    data = loader.load()
    return data



