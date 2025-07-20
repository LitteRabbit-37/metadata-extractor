extract_metadata.py

Description:

Produces a PDF report with each thumbnail and its metadata positioned below the image.

Browse a folder of images, generate thumbnails while maintaining the ratio, and extract for each image :

-   File name
-   Document Type
-   File size (MB)
-   Creation Date (EXIF)
-   Image size (pixels)
-   Image DPI (pixels/inch)

Usage:

```bash
    python extract_metadata.py /path/to/image_folder output.pdf
```

Requirements:

```bash
    pip install pillow exifread reportlab
```
