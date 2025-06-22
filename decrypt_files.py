import os
import binascii
import struct
from pathlib import Path
from itertools import product
from PIL import Image
import magic


def analyze_image(path):
    print(f"\n[==] Analyzing image: {path}")
    try:
        img = Image.open(path)
        print(f"[+] Format: {img.format}, Size: {img.size}, Mode: {img.mode}")
        for k, v in img.info.items():
            print(f"    - {k}: {v}")
    except Exception as e:
        print(f"[!] Failed to open image: {e}")


def extract_ascii(path, min_len=5):
    print("\n[==] Extracting ASCII strings:")
    data = Path(path).read_bytes()
    buf = b""
    for byte in data:
        if 32 <= byte <= 126:
            buf += bytes([byte])
        else:
            if len(buf) >= min_len:
                print(buf.decode(errors='ignore'))
            buf = b""
    if len(buf) >= min_len:
        print(buf.decode(errors='ignore'))


def check_bmp_trailing(path):
    print("\n[==] Checking for BMP trailing data:")
    with open(path, 'rb') as f:
        content = f.read()

    size_declared = struct.unpack('<I', content[2:6])[0]
    size_actual = len(content)

    if size_actual > size_declared:
        extra = size_actual - size_declared
        print(f"[+] Extra {extra} bytes found after BMP data")
        print(f"[+] Sample (hex): {binascii.hexlify(content[size_declared:size_declared+32]).decode()}")
    else:
        print("[-] No extra data detected")


def xor_decrypt(data, key):
    return bytes([b ^ key[i % 2] for i, b in enumerate(data)])


def brute_force_xor(file_path, output_dir):
    print(f"\n[==] Brute-forcing XOR keys on: {file_path}")
    data = Path(file_path).read_bytes()
    mime_checker = magic.Magic(mime=True)
    valid = []

    os.makedirs(output_dir, exist_ok=True)

    for k1, k2 in product(range(256), repeat=2):
        if 48 <= k1 <= 57 or 48 <= k2 <= 57:
            decrypted = xor_decrypt(data, (k1, k2))
            mtype = mime_checker.from_buffer(decrypted)

            if mtype not in ['application/octet-stream', 'data', 'application/zlib']:
                tag = f"{k1:02x}_{k2:02x}"
                out_path = os.path.join(output_dir, f"recovered_{tag}.bin")
                with open(out_path, 'wb') as out:
                    out.write(decrypted)
                print(f"[+] Valid file: {mtype} | Key: ({k1},{k2}) → {out_path}")
                valid.append((k1, k2, mtype))

    if not valid:
        print("[-] No valid headers detected.")
    else:
        print(f"[✓] {len(valid)} potential files recovered.")


if __name__ == "__main__":
    image_path = r"C:\Users\Ionut\Downloads\chapter4\images\set1\p3.jpg"
    encrypted_file = r"../chapter3/data1.bin"
    output_dir = r"../chapter3/decrypted_files"

    print("======== CYBERSHADOW FORENSICS SCRIPT ========")

    analyze_image(image_path)
    extract_ascii(image_path)
    check_bmp_trailing(image_path)
    brute_force_xor(encrypted_file, output_dir)
