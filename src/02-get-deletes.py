from collections import Counter
import itertools
from pydantic import BaseModel
from enum import Enum
from typing import Literal
import pandas as pd
import os
import math

DELETE_FILES = [".DS_Store"]
IGNORE_FOLDERS = [".git"]

class DuplicateGroup(BaseModel):
    file_md5: str 
    file_size_h: str
    file_count: int
    common_ancestor: str
    folder_file: list[tuple[str, str]]


class ResolutionCategory(Enum):
    same_folder_diff_name = "same_folder_diff_name"
    diff_folder_same_name = "diff_folder_same_name"
    
    
class Resolution(BaseModel):
    category: ResolutionCategory
    files: list[tuple[str, bool]]
    

def convert_size(size_bytes):
    """Convert bytes to a readable format (KB, MB, GB, etc.)."""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def find_common_prefix(paths):
    """Find the largest common prefix (base folder) in a list of paths."""
    if not paths:
        return ""
    
    # Split the paths into lists of directories
    split_paths = [p.split(os.sep) for p in paths]
    
    # Use zip to transpose the list of lists and iterate over corresponding parts
    common_parts = []
    for parts in zip(*split_paths):
        if all(part == parts[0] for part in parts):
            common_parts.append(parts[0])
        else:
            break
    
    # Join the common parts back into a single path
    return os.sep.join(common_parts)

def get_duplicate_volume(df):
    return convert_size(df[df.duplicated(subset='file_md5', keep='first')].file_size.sum())

def resolve_same_folder(dupl_group) -> Resolution:
    """Resolve duplicates in the same folder."""
    # Check if the files are the same
    folder_files = dupl_group.folder_file
    file_names = [f for _, f in folder_files]
    files = sorted(file_names, key=lambda x: (len(x), x.lower()), reverse=True)
    files = [os.path.join(dupl_group.common_ancestor, f) for f in files]
    files = [(f, True) if f == files[-1] else (f, False) for f in files] # keep the last file
    return Resolution(files=files, category=ResolutionCategory.same_folder_diff_name)

def resolve_same_name(dupl_group) -> Resolution:
    """Resolve duplicates with the same name."""
    # Check if the files are the same
    folder_files = dupl_group.folder_file
    base_file = folder_files[0][1]
    folders = [f for f, _ in folder_files]
    folders = sorted(folders, key=lambda x: (len(x), x.lower()), reverse=True)
    folders = [os.path.join(dupl_group.common_ancestor, f) for f in folders]
    files = [os.path.join(f, base_file) for f in folders]
    files = [(f, True) if f == files[-1] else (f, False) for f in files] # keep the last file
    return Resolution(files=files, category=ResolutionCategory.diff_folder_same_name)

def resolve(group: DuplicateGroup) -> Resolution:
    if all([f == "" for f, _ in group.folder_file]):
        # all files are in the same folder
        return resolve_same_folder(group)
    elif len(set([f for _, f in group.folder_file])) == 1:
        # all files have the same name
        return resolve_same_name(group)
    
    return None
    
    
def generate_deletion_list(dups: list[DuplicateGroup]) -> list[str]:
    """Generate a list of deletions for each duplicate group."""
    x = [dup.files for dup in dups]
    x = list(itertools.chain(*x))
    df = pd.DataFrame(x, columns=['file_path', 'keep'])
    df['delete'] = ~df['keep']
    return df[df['delete']]['file_path'].tolist()

df = pd.read_csv("files_report.csv")
df = df[~df.isna().any(axis=1) & (df.file_size > 0)]

duplicates = df[df.duplicated(subset='file_md5', keep=False)].sort_values(by='file_size', ascending=False)
duplicates['file_size_h'] = duplicates['file_size'].apply(convert_size)
duplicates['folder'] = duplicates['file_path'].apply(lambda x: os.path.dirname(x))
dupl_records = duplicates.groupby(['file_md5', 'file_size_h'], group_keys=False).apply(lambda x: x[['file_path', 'folder']].to_dict(orient='records')).to_dict()

## get all the duplicate groups
_dups = []
for ix, ((md5, size_h), records) in enumerate(dupl_records.items()):
    paths = [r['file_path'] for r in records]

    common_ancestor = find_common_prefix(paths)
    folder_and_file = [(r['folder'][len(common_ancestor):].lstrip(os.sep), os.path.basename(r['file_path']) )  for r in records]
    
    # how often these folders appear together
    _dups.append(DuplicateGroup(file_md5=md5, file_size_h=size_h, file_count=len(paths), common_ancestor=common_ancestor, folder_file=folder_and_file))
    

# Initialize a Counter to store pairwise occurrences
pairwise_counts = Counter()

dup_folders = [(d.common_ancestor, d.folder_file) for d in _dups if any(f != "" for f, _ in d.folder_file)]
dup_folders = [(x, *[i[0] for i in y]) for x, y in dup_folders]

for acs, *folders in dup_folders:
    sorted_folders = sorted(folders)
    unique_pairs = [(acs, *sorted(pair)) for pair in itertools.combinations(sorted_folders, 2) if pair[0] != pair[1]]
    pairwise_counts.update(unique_pairs)

# Printing the pairwise occurrences
vals = []
for pair, count in pairwise_counts.most_common():
    vals.append((*pair, count))
    
pairwise_df = pd.DataFrame(vals, columns=['common', 'folder1', 'folder2', 'count'])

easy_deletes = [resolve(d) for d in _dups if resolve(d) is not None and resolve(d).category == ResolutionCategory.same_folder_diff_name]
files_to_delete = generate_deletion_list(easy_deletes)

print(f"Total duplicate volume: {get_duplicate_volume(duplicates)}")
print(f"Total files to delete: {len(files_to_delete)}")
for f in files_to_delete:
    print(f)
    # os.remove(f)