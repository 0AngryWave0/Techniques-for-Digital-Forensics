import os
import zipfile
import argparse
import tempfile

# Try to import the 'magic' module for MIME type detection.
# If unavailable, set it to None to degrade gracefully.
try:
    import magic
except ImportError:
    magic = None

# Define common Office file extensions, which are ZIP-based but not treated as archives here.
OFFICE_EXTENSIONS = {'.docx', '.pptx', '.xlsx'}

# Returns the true MIME type and description of a file using libmagic.
def detect_file_type(file_path):
    if magic:
        try:
            mime = magic.from_file(file_path, mime=True)  # Get MIME type
            desc = magic.from_file(file_path)             # Get extended description
            return f"{mime} ({desc})"
        except Exception as e:
            return f"Unknown ({str(e)})"
    else:
        return "Unknown (magic module not installed)"

# Helper to format the tree structure line with prefix and connector symbols.
def format_tree_line(prefix, connector, label):
    return f"{prefix}{connector} {label}"

# Recursively scan a folder and return a list of tree lines with MIME type annotations.
def scan_folder(path, depth=None, current_depth=0, prefix="", is_last=True, allow_unzip=False):
    if depth is not None and current_depth > depth:
        return []

    tree_lines = []

    # Safely list directory contents
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return [format_tree_line(prefix, "└─" if is_last else "├─", "[Permission Denied]")]

    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        connector = "└─" if index == len(entries) - 1 else "├─"
        next_prefix = prefix + ("   " if index == len(entries) - 1 else "│  ")

        # Handle subdirectories recursively
        if os.path.isdir(full_path):
            tree_lines.append(format_tree_line(prefix, connector, f"📁 {entry}/"))
            subtree = scan_folder(full_path, depth, current_depth + 1, next_prefix, index == len(entries) - 1, allow_unzip)
            tree_lines.extend(subtree)

        # Handle regular files
        elif os.path.isfile(full_path):
            ext = os.path.splitext(entry)[1].lower()

            # Handle ZIP archives if --unzip flag is active
            if allow_unzip and zipfile.is_zipfile(full_path):
                if ext in OFFICE_EXTENSIONS:
                    # Skip Office formats
                    tree_lines.append(format_tree_line(prefix, connector, f"📦 {entry} — Office ZIP archive"))
                else:
                    # Unpack and scan contents in an isolated temp folder
                    tree_lines.append(format_tree_line(prefix, connector, f"📦 {entry} — ZIP archive"))
                    with tempfile.TemporaryDirectory() as tmpdir:
                        with zipfile.ZipFile(full_path, 'r') as zip_ref:
                            zip_ref.extractall(tmpdir)
                            for zindex, name in enumerate(sorted(zip_ref.namelist())):
                                zpath = os.path.join(tmpdir, name)
                                if os.path.isdir(zpath) or not os.path.isfile(zpath):
                                    continue
                                filetype = detect_file_type(zpath)
                                zconnector = "└─" if zindex == len(zip_ref.namelist()) - 1 else "├─"
                                tree_lines.append(format_tree_line(next_prefix, zconnector, f"📄 {name} — {filetype}"))
            else:
                # Normal file handling with MIME detection
                ftype = detect_file_type(full_path)
                tree_lines.append(format_tree_line(prefix, connector, f"📄 {entry} — {ftype}"))

        # Fallback for symbolic links or unknown file types
        else:
            tree_lines.append(format_tree_line(prefix, connector, f"❓ {entry}"))

    return tree_lines

# Write the full scan result to a text file, line by line.
def write_report(lines, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# Command-line interface and argument parsing
def main():
    parser = argparse.ArgumentParser(description="🔍 CYBERSHADOW Folder Scanner")
    parser.add_argument("folder", help="Folder to scan (e.g., chapter1)")
    parser.add_argument("--max_depth", help="'max' for full depth or int for level limit", default="1")
    parser.add_argument("--output", help="Save output to .txt file", default=None)
    parser.add_argument("--unzip", action="store_true", help="Optionally unzip ZIP archives (except Office formats)")
    args = parser.parse_args()

    # Interpret depth parameter
    depth = None if args.max_depth == "max" else int(args.max_depth)

    # Run the scan
    tree = scan_folder(args.folder, depth=depth, allow_unzip=args.unzip)

    # Save or print results
    if args.output:
        if not args.output.endswith(".txt"):
            print("[!] Please use a .txt extension for the output file.")
        else:
            write_report(tree, args.output)
    else:
        print("\n".join(tree))

# Entry point
if __name__ == "__main__":
    main()
