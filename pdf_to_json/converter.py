"""
PDF to JSON Converter

Converts PDF files to structured JSON format while preserving text and image positions.
"""

import os
import json
import base64
import fitz  # PyMuPDF
from openai import OpenAI
from typing import Optional, Dict, List


class PDFToJSONConverter:
    """
    Converter class to transform PDF files into structured JSON format.

    Features:
    - Preserves relative positions of text and images
    - Optional AI-powered image analysis using Qwen Vision model
    - Caches image analysis to avoid duplicate API calls
    - Supports table recognition in Markdown format
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the converter.

        Args:
            api_key: API key for Qwen Vision model (defaults to DASHSCOPE_API_KEY env var)
            base_url: Base URL for API (defaults to Aliyun DashScope)
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.image_cache = {}

    def analyze_image(self, image_base64: str, image_format: str) -> str:
        """
        Use Qwen Vision model to analyze image content.

        Args:
            image_base64: Base64 encoded image data
            image_format: Image format (png, jpg, etc.)

        Returns:
            Text description of the image content
        """
        if not self.api_key:
            return "Error: API key not configured"

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            # Construct data URL for the image
            data_url = f"data:image/{image_format};base64,{image_base64}"

            # Optimized prompt to ignore UI elements
            prompt = """请描述图片中的实质性内容信息，遵循以下规则：

1. 完全忽略所有装饰性元素：logo、icon、按钮、边框、背景图案等UI元素
2. 重点关注：文本内容、数据、表格、图表中的关键信息
3. 如果是表格，请用Markdown表格格式输出，保留表格结构
4. 如果是图表，描述其数据和趋势，不描述颜色、样式
5. 只输出有实际信息价值的内容，不描述视觉样式

请直接输出内容，不需要前缀说明。"""

            completion = client.chat.completions.create(
                model="qwen-vl-plus",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            return completion.choices[0].message.content
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def convert(self, pdf_path: str, analyze_images: bool = False,
                verbose: bool = False) -> Dict:
        """
        Convert PDF to structured JSON format.

        Args:
            pdf_path: Path to the PDF file
            analyze_images: Whether to use AI to analyze images
            verbose: Whether to print progress messages

        Returns:
            Dictionary containing structured PDF content
        """
        doc = fitz.open(pdf_path)
        result = {
            "total_pages": len(doc),
            "pages": []
        }

        # Clear image cache for new conversion
        self.image_cache.clear()

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_content = {
                "page_number": page_num + 1
            }

            # Get all text blocks with positions
            text_blocks = page.get_text("dict")["blocks"]

            # Get all images with positions
            image_list = page.get_images()

            # Collect all elements with their vertical positions
            elements = []

            # Process text blocks
            for block in text_blocks:
                if block["type"] == 0:  # Text block
                    # Extract text from lines
                    text_content = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text_content += span.get("text", "")
                        text_content += "\n"

                    if text_content.strip():
                        elements.append({
                            "type": "text",
                            "content": text_content.strip(),
                            "bbox": block["bbox"],
                            "y_position": block["bbox"][1]
                        })

            # Process images
            for img_index, img in enumerate(image_list):
                xref = img[0]
                img_bbox = page.get_image_bbox(img[7])

                image_element = {
                    "type": "image",
                    "bbox": [img_bbox.x0, img_bbox.y0, img_bbox.x1, img_bbox.y1],
                    "y_position": img_bbox.y0,
                    "width": img_bbox.width,
                    "height": img_bbox.height,
                    "xref": xref
                }

                # Analyze image with AI if enabled
                if analyze_images:
                    # Check cache to avoid duplicate analysis
                    if xref in self.image_cache:
                        if verbose:
                            print(f"Using cached analysis for image xref={xref} on page {page_num + 1}")
                        image_element["ai_description"] = self.image_cache[xref]
                    else:
                        # First time encountering this image
                        if verbose:
                            print(f"Analyzing image {img_index + 1} (xref={xref}) on page {page_num + 1}...")

                        # Get image data
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Encode image to base64
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

                        description = self.analyze_image(image_base64, image_ext)
                        image_element["ai_description"] = description

                        # Cache the result
                        self.image_cache[xref] = description

                elements.append(image_element)

            # Sort elements by vertical position (top to bottom)
            elements.sort(key=lambda x: x["y_position"])

            # Convert elements to simplified paragraphs
            paragraphs = []
            for elem in elements:
                if elem["type"] == "text":
                    paragraphs.append(elem["content"])
                elif elem["type"] == "image" and "ai_description" in elem:
                    paragraphs.append(f"【此处为原图片解析信息】\n{elem['ai_description']}")

            page_content["paragraphs"] = paragraphs
            result["pages"].append(page_content)

        doc.close()
        return result

    def convert_to_json_string(self, pdf_path: str, analyze_images: bool = False,
                              verbose: bool = False, indent: int = 2) -> str:
        """
        Convert PDF to JSON string.

        Args:
            pdf_path: Path to the PDF file
            analyze_images: Whether to use AI to analyze images
            verbose: Whether to print progress messages
            indent: JSON indentation level

        Returns:
            JSON string representation of the PDF content
        """
        result = self.convert(pdf_path, analyze_images, verbose)
        return json.dumps(result, ensure_ascii=False, indent=indent)

    def convert_to_file(self, pdf_path: str, output_path: str,
                       analyze_images: bool = False, verbose: bool = False,
                       indent: int = 2) -> None:
        """
        Convert PDF to JSON and save to file.

        Args:
            pdf_path: Path to the PDF file
            output_path: Path to save the JSON output
            analyze_images: Whether to use AI to analyze images
            verbose: Whether to print progress messages
            indent: JSON indentation level
        """
        json_string = self.convert_to_json_string(pdf_path, analyze_images, verbose, indent)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_string)
        if verbose:
            print(f"JSON output saved to: {output_path}")
