import io
from PIL import Image, ImageOps


def scrub_image_exif(image_bytes: bytes, max_dimension: int = 2560) -> tuple[bytes, str]:
    """
    Strips 100% of EXIF tags (GPS coordinates, camera model, exact timestamp, software)
    from uploaded images in-memory via Pillow (BytesIO).
    
    OpSec Principle:
    Smartphone cameras embed extensive hardware and location telemetry into photo files.
    This function rebuilds a raw pixel buffer from memory, discarding any header metadata
    before the media is ever transmitted to Telegram servers.
    
    Returns:
        tuple[bytes, str]: (scrubbed_image_bytes, mime_type)
    """
    with Image.open(io.BytesIO(image_bytes)) as img:
        # Correct orientation based on EXIF before stripping it
        img = ImageOps.exif_transpose(img) or img
        
        orig_format = (img.format or "JPEG").upper()
        
        # Downscale oversized images slightly to optimize memory and upload speed
        if max(img.size) > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
        # Standardize formats: PNG for transparent, JPEG for RGB
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            target_format = "PNG"
            mime_type = "image/png"
            clean_mode = "RGBA"
            clean_img = img.convert("RGBA")
        else:
            target_format = "JPEG"
            mime_type = "image/jpeg"
            clean_mode = "RGB"
            clean_img = img.convert("RGB")
            
        # Reconstruct pure in-memory pixel buffer without any inherited metadata dictionaries
        purged_image = Image.frombytes(
            clean_mode,
            clean_img.size,
            clean_img.tobytes()
        )
        
        output_buffer = io.BytesIO()
        if target_format == "JPEG":
            purged_image.save(output_buffer, format="JPEG", quality=92, optimize=True)
        else:
            purged_image.save(output_buffer, format="PNG", optimize=True)
            
        return output_buffer.getvalue(), mime_type
