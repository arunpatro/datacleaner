    import os
    import hashlib
    import json

    def calculate_md5(file_path):
        """Calculate the MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def list_files_and_hashes(directory):
        """List all files in the directory and calculate their MD5 hash."""
        files_data = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_hash = calculate_md5(file_path)
                files_data.append({
                    'path': file_path,
                    'hash': file_hash,
                    'size': os.path.getsize(file_path),
                    'last_modified': os.path.getmtime(file_path)
                })
        return files_data

    def save_data_to_json(data, filename):
        """Save the file data to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def load_data_from_json(filename):
        """Load file data from a JSON file."""
        with open(filename, 'r') as f:
            return json.load(f)

    def detect_duplicates(files_data):
        """Detect duplicate files based on their MD5 hash."""
        hash_dict = {}
        duplicates = []
        for file in files_data:
            file_hash = file['hash']
            if file_hash in hash_dict:
                duplicates.append((hash_dict[file_hash], file))
            else:
                hash_dict[file_hash] = file
        return duplicates

    def main():
        directory = "/Users/arunpatro/My Drive"#input("Enter the directory to scan: ")
        output_file = "file_data.json"

        # List files and calculate their MD5 hash
        files_data = list_files_and_hashes(directory)

        # Save data to JSON
        save_data_to_json(files_data, output_file)
        print(f"File data saved to {output_file}")

        # Load data from JSON
        loaded_data = load_data_from_json(output_file)

        # Detect duplicates
        duplicates = detect_duplicates(loaded_data)
        if duplicates:
            print("Duplicate files found:")
            for dup in duplicates:
                print(f"Original: {dup[0]['path']} <--> Duplicate: {dup[1]['path']}")
        else:
            print("No duplicates found.")

    if __name__ == "__main__":
        main()
