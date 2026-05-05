import io
from PIL import Image


class ThumbnailService:
    def generate(self, image_data: bytes, max_size: tuple[int, int] = (400, 400)) -> bytes:
        # Use Pillow to open image from bytes
        with Image.open(io.BytesIO(image_data)) as img:
            # Resize preserving aspect ratio (use Image.thumbnail())
            img.thumbnail(max_size)

            # Save to bytes buffer as same format
            # Determine format based on image format (JPEG for jpeg, PNG for png, WebP for webp)
            fmt = img.format if img.format else "JPEG"

            # Re-save to bytes
            out_buffer = io.BytesIO()
            img.save(out_buffer, format=fmt)
            return out_buffer.getvalue()

    def get_image_dimensions(self, image_data: bytes) -> tuple[int, int]:
        # Use Pillow to open image and return (width, height)
        with Image.open(io.BytesIO(image_data)) as img:
            return img.width, img.height
