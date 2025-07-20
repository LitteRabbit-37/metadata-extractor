import os
import sys
from datetime import datetime

import exifread
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 0.5 * inch
MAX_THUMB_DIM = 5 * inch
LINE_HEIGHT = 14
ENTRY_SPACING = 0.3 * inch


def format_filesize(bytes_size):
    return f"{bytes_size / (1024*1024):.2f} MB"


def format_datetime(dt):
    return dt.strftime("%d %B %Y at %H:%M")


def get_file_creation_date(path):
    stat = os.stat(path)
    try:
        ctime = stat.st_birthtime
    except AttributeError:
        ctime = stat.st_ctime
    return datetime.fromtimestamp(ctime)


def get_exif_tags(path):
    with open(path, 'rb') as f:
        return exifread.process_file(f, details=False)


def extract_creation_date(path):
    tags = get_exif_tags(path)
    # Date priority EXIF DateTimeOriginal
    date_tag = tags.get('EXIF DateTimeOriginal') or tags.get('Image DateTime')
    if date_tag:
        try:
            dt = datetime.strptime(str(date_tag.values), '%Y:%m:%d %H:%M:%S')
            return dt
        except Exception:
            pass
    return get_file_creation_date(path)


def generate_thumbnails(folder, thumb_dir):
    os.makedirs(thumb_dir, exist_ok=True)
    thumbs = {}
    for fname in sorted(os.listdir(folder)):
        fpath = os.path.join(folder, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            img = Image.open(fpath)
        except IOError:
            continue
        # Keep ratio and resize to MAX_THUMB_DIM
        img.thumbnail((MAX_THUMB_DIM, MAX_THUMB_DIM))
        thumb_path = os.path.join(thumb_dir, fname)
        img.save(thumb_path)
        thumbs[fname] = {
            'path': thumb_path,
            'size': img.size  # (width, height) en pixels
        }
    return thumbs


def collect_metadata(folder, thumbs):
    entries = []
    for fname, thumb_info in thumbs.items():
        fpath = os.path.join(folder, fname)
        img = Image.open(fpath)
        file_size = format_filesize(os.path.getsize(fpath))
        doc_type = img.format
        creation_dt = extract_creation_date(fpath)
        creation = format_datetime(creation_dt)
        width, height = img.size
        image_size = f"{width} x {height}"
        dpi_info = img.info.get('dpi')
        if dpi_info:
            dpi = f"{dpi_info[0]} x {dpi_info[1]} dpi"
        else:
            tags = get_exif_tags(fpath)
            xres = tags.get('Image XResolution')
            unit = tags.get('Image ResolutionUnit')
            if xres and unit:
                dpi = f"{xres.values[0]} {unit.values}"
            else:
                dpi = "Unknown"
        entries.append({
            'filename': fname,
            'doc_type': doc_type,
            'file_size': file_size,
            'creation_date': creation,
            'image_size': image_size,
            'dpi': dpi,
            'thumb_path': thumb_info['path'],
            'thumb_size': thumb_info['size']
        })
    return entries


def create_pdf_report(entries, output_pdf):
    c = canvas.Canvas(output_pdf, pagesize=A4)
    x = MARGIN
    y = PAGE_HEIGHT - MARGIN
    for entry in entries:
        thumb_w_px, thumb_h_px = entry['thumb_size']
        # Convert pixels to points (1 point = 1/72 inch)
        thumb_w = thumb_w_px
        thumb_h = thumb_h_px
        needed_space = thumb_h + (6 * LINE_HEIGHT) + ENTRY_SPACING
        if y < MARGIN + needed_space:
            c.showPage()
            y = PAGE_HEIGHT - MARGIN
        # Draw thumbnail
        c.drawImage(entry['thumb_path'], x, y - thumb_h,
                    width=thumb_w, height=thumb_h)
        # Draw metadata under the thumbnail
        text_x = x
        text_y = y - thumb_h - LINE_HEIGHT
        c.setFont('Helvetica', 10)
        for line in [
            f"File name: {entry['filename']}",
            f"Document Type: {entry['doc_type']}",
            f"File size: {entry['file_size']}",
            f"Creation Date: {entry['creation_date']}",
            f"Image size: {entry['image_size']}",
            f"Image DPI: {entry['dpi']}"
        ]:
            c.drawString(text_x, text_y, line)
            text_y -= LINE_HEIGHT
        # Update y for next spaced entry
        y = text_y - ENTRY_SPACING
    c.save()
    print(f"PDF report generated: {output_pdf}")


def main(folder, output_pdf):
    out_dir = os.path.dirname(os.path.abspath(output_pdf)) or '.'
    thumb_dir = os.path.join(out_dir, 'thumbnails')
    thumbs = generate_thumbnails(folder, thumb_dir)
    entries = collect_metadata(folder, thumbs)
    create_pdf_report(entries, output_pdf)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python extract_metadata.py /path/to/folder output.pdf")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
