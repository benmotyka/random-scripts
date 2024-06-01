This script filters out items from the first column of CSV file that are present in the first column of second CSV file, and creates a new file as a result.

# Usage
```sh
python3 ./script.py input_file1.csv input_file2.csv output_file.csv --case-sensitive
```

where:
- `input_file1.csv` path to the first CSV file (from which items will be deleted in a new file)
- `input_file2.csv` path to the second CSV file (items that should be deleted)
- `output_file.csv` path to the output CSV file
- `--case-sensitive` flag to enable case-sensitive comparison (optional)
