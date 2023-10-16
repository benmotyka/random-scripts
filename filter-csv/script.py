import csv

def filter_items(input_file1, input_file2, output_file, case_sensitive):
    with open(input_file1, 'r') as file1, open(input_file2, 'r') as file2:
        items_file1 = set()
        for row in csv.reader(file1):
            if row:
                item = row[0]
                if case_sensitive == 'n':
                    item = item.lower()
                items_file1.add(item)  # Convert to lowercase
        
        items_file2 = set()
        for row in csv.reader(file2):
            if row:
                item = row[0]
                if case_sensitive == 'n':
                    item = item.lower()
                items_file2.add(item)  # Convert to lowercase
        
        filtered_items = list(items_file1 - items_file2)
        
        with open(output_file, 'w', newline='') as output_csv:
            writer = csv.writer(output_csv)
            for item in filtered_items:
                writer.writerow([item])

if __name__ == "__main__":
    print("This script filters out items from the first column of CSV file that are present in the first column of second CSV file, and creates a new file as a result.")
    input_file1 = input("Enter the path to the first CSV file (from which items will be deleted in a new file): ")
    input_file2 = input("Enter the path to the second CSV file (items that should be deleted): ")
    output_file = input("Enter the path for the output CSV file: ")
    case_sensitive = input("Should the comparison of the items be case sensitive? (Y/n): ")

    filter_items(input_file1, input_file2, output_file, case_sensitive)
    print(f"Filtered items have been saved to {output_file}.")
