import hashlib
import json
import zipfile
from pathlib import Path

from PIL import Image

MANIFEST_NAME = "manifest.json"

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".wmf", ".emf"}


def _image_dir(md_path: str | Path) -> Path:
    return Path(str(md_path) + "_images")


def _extract_from_docx(source_path: Path, save_dir: Path) -> list[dict]:
    images = []
    try:
        with zipfile.ZipFile(source_path, "r") as z:
            for name in z.namelist():
                if not name.startswith("word/media/"):
                    continue
                data = z.read(name)
                raw_ext = Path(name).suffix.lower()
                if raw_ext not in _IMAGE_EXTS:
                    continue
                md5 = hashlib.md5(data).hexdigest()
                dest = save_dir / f"{md5}{raw_ext}"
                if dest.exists():
                    img = Image.open(dest)
                else:
                    dest.write_bytes(data)
                    img = Image.open(dest)
                images.append({
                    "md5": md5,
                    "ext": raw_ext,
                    "width": img.width,
                    "height": img.height,
                    "size_bytes": len(data),
                })
    except Exception:
        pass
    return images


def extract_images_from_source(source_path: str | Path, md_path: str | Path) -> list[dict]:
    """Extract embedded images from a source file into {md_path}_images/.

    Supports DOCX (via zipfile). PDF image extraction requires PyMuPDF (not yet integrated).
    Returns list of {md5, ext, width, height, size_bytes}.
    """
    source_path = Path(source_path)
    md_path = Path(md_path)
    save_dir = _image_dir(md_path)
    save_dir.mkdir(parents=True, exist_ok=True)

    ext = source_path.suffix.lower()
    if ext == ".docx":
        images = _extract_from_docx(source_path, save_dir)
    else:
        images = []

    if images:
        (save_dir / MANIFEST_NAME).write_text(
            json.dumps(images, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return images


def get_image_manifest(md_path: str | Path) -> list[dict]:
    manifest = _image_dir(md_path) / MANIFEST_NAME
    if manifest.exists():
        return json.loads(manifest.read_text(encoding="utf-8"))
    return []


def get_image_bytes(md_path: str | Path, md5: str) -> bytes | None:
    img_dir = _image_dir(md_path)
    for f in img_dir.iterdir():
        if f.is_file() and f.stem == md5 and f.name != MANIFEST_NAME:
            return f.read_bytes()
    return None


def get_image_info(md_path: str | Path, md5: str) -> dict | None:
    for item in get_image_manifest(md_path):
        if item["md5"] == md5:
            return item
    return None
