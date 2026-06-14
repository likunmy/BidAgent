import re
from pathlib import Path

from pydantic import BaseModel

from app.agent.tools import image_extractor


class LoadFileInput(BaseModel):
    file_path: str
    section_heading: str | None = None


class ImagePlaceholder(BaseModel):
    md5: str
    width: int
    height: int
    size_bytes: int
    path: str


class LoadFileOutput(BaseModel):
    content: str
    images: list[ImagePlaceholder]


def load_file(input_data: LoadFileInput) -> LoadFileOutput:
    """Load an MD file's content, optionally filtered by section heading.

    Embedded image references are replaced with structured placeholders.
    """
    md_path = Path(input_data.file_path)
    if not md_path.exists():
        raise FileNotFoundError(f"文件不存在: {input_data.file_path}")
    if md_path.suffix != ".md":
        raise ValueError(f"仅支持 MD 文件: {input_data.file_path}")

    content = md_path.read_text(encoding="utf-8")

    # Filter by section heading if specified
    if input_data.section_heading:
        content = _extract_section(content, input_data.section_heading)

    # Replace image references with placeholders
    content, images = _replace_images(content, md_path)

    return LoadFileOutput(content=content, images=images)


def _extract_section(content: str, heading: str) -> str:
    """Extract content under a given Markdown heading (any level)."""
    pattern = re.compile(
        r"^(#{1,6})\s*" + re.escape(heading) + r"\s*$",
        re.MULTILINE,
    )
    match = pattern.search(content)
    if not match:
        return ""

    heading_level = len(match.group(1))
    start = match.end()

    # Find next heading at same or higher level
    next_match = re.search(
        rf"^#{{1,{heading_level}}}\s",
        content[start:],
        re.MULTILINE,
    )
    end = start + next_match.start() if next_match else len(content)

    return content[start:end].strip()


# Regex to match standard markdown images: ![alt](path)
_IMAGE_PATTERN = re.compile(r"!\[.*?\]\(([^)]+)\)")


def _replace_images(content: str, md_path: Path) -> tuple[str, list[ImagePlaceholder]]:
    """Replace markdown image references with structured placeholders.

    Returns (updated_content, image_list).
    """
    images: list[ImagePlaceholder] = []
    manifest = image_extractor.get_image_manifest(md_path)
    manifest_by_name: dict[str, dict] = {}
    for item in manifest:
        md5 = item["md5"]
        for ext in [item["ext"], f".{item['ext'].lstrip('.').upper()}"]:
            manifest_by_name[f"{md5}{ext}"] = item

    def replace_match(m: re.Match) -> str:
        img_path_str = m.group(1)
        img_path = Path(img_path_str)

        # Try to match by filename stem (md5)
        for fname, info in manifest_by_name.items():
            if Path(fname).stem == img_path.stem:
                ph = ImagePlaceholder(
                    md5=info["md5"],
                    width=info["width"],
                    height=info["height"],
                    size_bytes=info["size_bytes"],
                    path=str(md_path),
                )
                if ph not in images:
                    images.append(ph)
                return f"[图: md5={info['md5']}, 尺寸={info['width']}x{info['height']}]"
            if fname == img_path_str or fname == img_path.name:
                ph = ImagePlaceholder(
                    md5=info["md5"],
                    width=info["width"],
                    height=info["height"],
                    size_bytes=info["size_bytes"],
                    path=str(md_path),
                )
                if ph not in images:
                    images.append(ph)
                return f"[图: md5={info['md5']}, 尺寸={info['width']}x{info['height']}]"

        # No match in manifest — pass through as-is
        return m.group(0)

    content = _IMAGE_PATTERN.sub(replace_match, content)
    return content, images
