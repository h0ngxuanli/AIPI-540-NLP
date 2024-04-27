from transformers import NougatProcessor, VisionEncoderDecoderModel
import torch.cuda
import io
import base64
from PIL import Image
from typing import Dict, Any

class EndpointHandler():
    def __init__(self, path="facebook/nougat-base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = NougatProcessor.from_pretrained(path)
        self.model = VisionEncoderDecoderModel.from_pretrained(path)
        self.model = self.model.to(self.device)
    def __call__(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            data (Dict): The payload with the text prompt 
        and generation parameters.
        """
        # Get inputs
        input = data.pop("inputs", None)
        parameters = data.pop("parameters", None)
        fix_markdown = data.pop("fix_markdown", None)
        if input is None:
            raise ValueError("Missing image.")
        # autoregressively generate tokens, with custom stopping criteria (as defined by the Nougat authors)
        binary_data = base64.b64decode(input)

        image = Image.open(io.BytesIO(binary_data))
        pixel_values = self.processor(images= image, return_tensors="pt").pixel_values
        outputs = self.model.generate(inputs = pixel_values.to(self.device), 
                                      bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                                      **parameters)
        generated = self.processor.batch_decode(outputs[0], skip_special_tokens=True)[0]
        prediction = self.processor.post_process_generation(generated, fix_markdown=fix_markdown)

        return {"generated_text": prediction}