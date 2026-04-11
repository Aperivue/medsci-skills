#!/usr/bin/env python3
"""
AI Image Generation via Gemini API (optional supplementary tool).
Visual abstracts and figures can be created without this tool.

Usage:
    python generate_image.py "prompt text" --output path/to/output.png
    python generate_image.py "prompt text" --output path/to/output.png --aspect 16:9
    python generate_image.py "CT-guided lung biopsy procedure" -o biopsy.png --style medical

Environment variable required:
    GEMINI_API_KEY
"""

import argparse
import base64
import os
import sys
from pathlib import Path

MEDICAL_STYLE_PREFIX = (
    "Create a clean medical illustration in the style of Servier Medical Art. "
    "Use flat vector-style graphics with clear outlines. No text in the image. "
    "White or transparent background. Anatomically accurate but simplified. "
    "Suitable for use in a peer-reviewed journal graphical abstract. "
)


def generate_image(prompt: str, output_path: str, aspect_ratio: str = "1:1",
                   style: str | None = None) -> str:
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    model = genai.GenerativeModel("gemini-2.0-flash-preview-image-generation")

    # Prepend medical style prefix if requested
    full_prompt = prompt
    if style == "medical":
        full_prompt = MEDICAL_STYLE_PREFIX + prompt

    # Include aspect ratio instruction in the prompt
    if aspect_ratio != "1:1":
        full_prompt += f" Output aspect ratio: {aspect_ratio}."

    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="image/png",
        ),
    )

    # Extract image data from response
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                image_data = part.inline_data.data
                Path(output_path).write_bytes(image_data)
                print(f"Image saved: {output_path}", file=sys.stderr)
                print(output_path)
                return output_path

    # Fallback: check if response has image in different format
    print("Error: No image data in response.", file=sys.stderr)
    if response.text:
        print(f"Response text: {response.text[:200]}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Generate images via Gemini API")
    parser.add_argument("prompt", help="Image generation prompt")
    parser.add_argument("--output", "-o", required=True, help="Output file path (.png)")
    parser.add_argument(
        "--aspect",
        default="1:1",
        choices=["1:1", "16:9", "9:16", "4:3", "3:4"],
        help="Aspect ratio (default: 1:1)",
    )
    parser.add_argument(
        "--style",
        choices=["medical"],
        help="Prepend a style prefix to the prompt (medical: flat vector medical illustration)",
    )
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not set", file=sys.stderr)
        print("This tool is optional — visual abstracts can be created without it.", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generate_image(args.prompt, str(output_path), args.aspect, args.style)


if __name__ == "__main__":
    main()
