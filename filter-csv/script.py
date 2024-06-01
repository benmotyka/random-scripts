import argparse
import csv

def filter_items(input_file1, input_file2, output_file, case_sensitive):
    with open(input_file1, 'r') as file1, open(input_file2, 'r') as file2:
        items_file1 = set()
        for row in csv.reader(file1):
            if row:
                item = row[0]
                if not case_sensitive:
                    item = item.lower()
                items_file1.add(item)  # Convert to lowercase
        
        items_file2 = set()
        for row in csv.reader(file2):
            if row:
                item = row[0]
                if not case_sensitive:
                    item = item.lower()
                items_file2.add(item)  # Convert to lowercase
        
        filtered_items = list(items_file1 - items_file2)
        
        with open(output_file, 'w', newline='') as output_csv:
            writer = csv.writer(output_csv)
            for item in filtered_items:
                writer.writerow([item])

def main():
    parser = argparse.ArgumentParser(description="Filters out items from the first column of one CSV file that are present in the first column of another CSV file, and creates a new file as a result.")
    parser.add_argument("input_file1", help="Path to the first CSV file (from which items will be deleted in a new file)")
    parser.add_argument("input_file2", help="Path to the second CSV file (items that should be deleted)")
    parser.add_argument("output_file", help="Path to the output CSV file")
    parser.add_argument("--case-sensitive", dest="case_sensitive", action="store_true", help="Make the comparison of the items case sensitive")

    args = parser.parse_args()
    filter_items(args.input_file1, args.input_file2, args.output_file, args.case_sensitive)
    print(f"Filtered items have been saved to {args.output_file}.")

if __name__ == "__main__":
    main()
