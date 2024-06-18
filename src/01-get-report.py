import os
import hashlib
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool, cpu_count

def calculate_md5(file_path, chunk_size=8192):
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    except IOError:
        return None

def get_file_details(file_path):
    """Get file details including size and MD5 hash."""
    try:
        file_size = os.path.getsize(file_path)
        file_md5 = calculate_md5(file_path)
        is_symlink = os.path.islink(file_path)
        return {
            "file_path": file_path,
            "file_size": file_size,
            "file_md5": file_md5,
            "is_symlink": is_symlink
        }
    except OSError:
        return None

def scan_directory(directory):
    """Scan directory and gather file paths."""
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    return file_paths

def process_files_in_parallel(file_paths):
    """Process files in parallel to get their details."""
    with Pool(cpu_count()) as pool:
        file_details = list(tqdm(pool.imap(get_file_details, file_paths), total=len(file_paths), desc="Processing files"))
    # Filter out None results from failed file processing
    file_details = [detail for detail in file_details if detail is not None]
    return file_details

def create_csv(file_details, output_csv):
    """Create a CSV file with file details sorted by size."""
    df = pd.DataFrame(file_details)
    df = df.sort_values(by="file_size", ascending=False)
    df.to_csv(output_csv, index=False)

def main(directory, output_csv):
    """Main function to scan directory and create CSV."""
    print("Scanning directory for files...")
    file_paths = scan_directory(directory)
    print(f"Found {len(file_paths)} files. Processing files...")
    file_details = process_files_in_parallel(file_paths)
    print("Creating CSV file...")
    create_csv(file_details, output_csv)
    print(f"Operation completed. CSV file saved to {output_csv}")

if __name__ == "__main__":
    directory_to_scan = "/Users/arunpatro/My Drive"  # Update this to your directory
    output_csv_path = "files_report.csv"
    main(directory_to_scan, output_csv_path)
