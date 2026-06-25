import os
import platform
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

_PHOTO_DIR = Path(__file__).parent.parent / "photos"

if platform.system() == "Windows":
    _SOFFICE = r"E:\libre\LibreOffice\program\soffice.exe"
else:
    _SOFFICE = "soffice"


def extract_photo(doc_path, cadre_id,
                  photo_dir: Path = None,
                  soffice: str = None) -> Tuple[Optional[str], Optional[str]]:
    """从干部任免表中提取照片。

    返回 (photo_path, error_msg)，成功时 error_msg 为 None。
    """
    out_dir = photo_dir or _PHOTO_DIR
    out_dir.mkdir(exist_ok=True)

    file_path = Path(doc_path)
    ext = file_path.suffix.lower()

    if ext == ".docx":
        return _extract_from_docx(file_path, cadre_id, out_dir)
    elif ext == ".doc":
        return _extract_from_doc(file_path, cadre_id, out_dir,
                                 soffice or _SOFFICE)
    else:
        return None, f"不支持的格式: {ext}"


def _extract_from_docx(docx_path: Path, cadre_id: str,
                       out_dir: Path) -> Tuple[Optional[str], Optional[str]]:
    """.docx 是 ZIP 压缩包，直接解压提取 word/media/ 中的图片。"""
    try:
        with zipfile.ZipFile(docx_path) as z:
            images = [f for f in z.namelist()
                      if "media/" in f
                      and f.rsplit(".", 1)[-1].lower() in ("jpg", "jpeg", "png")]
            if not images:
                return None, "文档中无图片"
            img_name = images[0]
            img_ext = Path(img_name).suffix
            out_path = out_dir / f"{cadre_id}{img_ext}"
            out_path.write_bytes(z.read(img_name))
            return str(out_path), None
    except zipfile.BadZipFile:
        return None, "不是有效的 .docx 文件"


def _extract_from_doc(doc_path: Path, cadre_id: str,
                      out_dir: Path,
                      soffice: str) -> Tuple[Optional[str], Optional[str]]:
    """.doc → 用 LibreOffice 转换为 .docx → 再提取图片。"""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [soffice, "--headless", "--convert-to", "docx",
                 "--outdir", tmp, str(doc_path)],
                timeout=60,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return None, f"LibreOffice 返回码 {result.returncode}"

            docx_files = list(Path(tmp).glob("*.docx"))
            if not docx_files:
                return None, "LibreOffice 转换失败: 未生成 .docx 文件"

            return _extract_from_docx(docx_files[0], cadre_id, out_dir)
    except subprocess.TimeoutExpired:
        return None, "LibreOffice 转换超时 (60s)"
    except FileNotFoundError:
        return None, f"找不到 LibreOffice: {soffice}"
