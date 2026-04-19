import fitz
import json
import sys
import os

def generate_layout_map(pdf_path, output_json):
    doc = fitz.open(pdf_path)
    layout_map = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        items = []
        
        # 1. Text blocks with font info and bbox
        try:
            raw_dict = page.get_text("dict")
            blocks = raw_dict.get("blocks", [])
            for b in blocks:
                if b["type"] == 0: # text
                    for line in b["lines"]:
                        for span in line["spans"]:
                            items.append({
                                "type": "text",
                                "bbox": span["bbox"],
                                "text": span["text"],
                                "size": span["size"],
                                "font": span["font"]
                            })
        except Exception as e:
            print(f"Error extracting text on page {page_num+1}: {e}")
        
        # 2. Images with bbox
        try:
            image_info = page.get_image_info()
            for img in image_info:
                items.append({
                    "type": "image",
                    "bbox": img["bbox"],
                    "width": img["width"],
                    "height": img["height"]
                })
        except Exception as e:
            print(f"Error extracting images on page {page_num+1}: {e}")
            
        # Sort by vertical position (y0)
        items.sort(key=lambda x: x["bbox"][1])
        
        layout_map.append({
            "page": page_num + 1,
            "items": items
        })

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(layout_map, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_layout_map.py <pdf_path> <output_json>")
        sys.exit(1)
    generate_layout_map(sys.argv[1], sys.argv[2])
