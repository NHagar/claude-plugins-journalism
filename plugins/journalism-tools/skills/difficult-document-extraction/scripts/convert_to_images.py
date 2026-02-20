#!/usr/bin/env python3
"""
Convert PDF or multi-page image documents to individual page images.
Supports PDF, TIFF, and common image formats.
"""

import argparse
import sys
from pathlib import Path


def convert_pdf(input_path: Path, output_dir: Path, dpi: int, fmt: str) -> list[Path]:
    """Convert PDF pages to images using pdf2image."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        print("Installing pdf2image...", file=sys.stderr)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pdf2image", "-q"])
        from pdf2image import convert_from_path
    
    images = convert_from_path(input_path, dpi=dpi)
    output_paths = []
    
    for i, image in enumerate(images, 1):
        output_path = output_dir / f"page_{i:03d}.{fmt}"
        image.save(output_path, fmt.upper())
        output_paths.append(output_path)
        print(f"  Saved: {output_path}")
    
    return output_paths


def convert_tiff(input_path: Path, output_dir: Path, fmt: str) -> list[Path]:
    """Convert multi-page TIFF to individual images."""
    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow...", file=sys.stderr)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
        from PIL import Image
    
    output_paths = []
    with Image.open(input_path) as img:
        for i in range(getattr(img, 'n_frames', 1)):
            img.seek(i)
            output_path = output_dir / f"page_{i+1:03d}.{fmt}"
            img.save(output_path, fmt.upper())
            output_paths.append(output_path)
            print(f"  Saved: {output_path}")
    
    return output_paths


def convert_image(input_path: Path, output_dir: Path, fmt: str) -> list[Path]:
    """Copy/convert single image to output directory."""
    try:
        from PIL import Image
    except ImportError:
        print("Installing Pillow...", file=sys.stderr)
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
        from PIL import Image
    
    output_path = output_dir / f"page_001.{fmt}"
    with Image.open(input_path) as img:
        img.save(output_path, fmt.upper())
    print(f"  Saved: {output_path}")
    return [output_path]


def main():
    parser = argparse.ArgumentParser(
        description="Convert documents to page images for transcription"
    )
    parser.add_argument("input", type=Path, help="Input PDF, TIFF, or image file")
    parser.add_argument(
        "--output-dir", "-o", type=Path, default=Path("./pages"),
        help="Output directory for page images (default: ./pages)"
    )
    parser.add_argument(
        "--dpi", type=int, default=200,
        help="Resolution for PDF rendering (default: 200)"
    )
    parser.add_argument(
        "--format", "-f", choices=["png", "jpg"], default="png",
        help="Output image format (default: png)"
    )
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    suffix = args.input.suffix.lower()
    print(f"Converting: {args.input}")
    
    if suffix == ".pdf":
        output_paths = convert_pdf(args.input, args.output_dir, args.dpi, args.format)
    elif suffix in (".tif", ".tiff"):
        output_paths = convert_tiff(args.input, args.output_dir, args.format)
    elif suffix in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
        output_paths = convert_image(args.input, args.output_dir, args.format)
    else:
        print(f"Error: Unsupported file type: {suffix}", file=sys.stderr)
        sys.exit(1)
    
    print(f"\nConverted {len(output_paths)} page(s) to {args.output_dir}/")


if __name__ == "__main__":
    main()