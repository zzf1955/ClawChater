"""图片相似度计算模块"""
import imagehash
from PIL import Image
from pathlib import Path


def compute_phash(image_path: Path) -> str:
    """计算图片的感知哈希"""
    img = Image.open(image_path)
    return str(imagehash.phash(img))


def hash_similarity(hash1: str, hash2: str) -> float:
    """计算两个哈希的相似度 (0-1)"""
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    # hamming距离，最大64位
    distance = h1 - h2
    return 1.0 - (distance / 64.0)
