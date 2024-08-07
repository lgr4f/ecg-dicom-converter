import argparse
import os
from .extract_ecg_and_metadata import extract_data
from .load_to_dicom import create_dicom_ecg

def process_file(input_file, output_dir):
    # Extract ECG data and metadata
    data, metadata = extract_data(input_file)
    # Create output file path
    output_file = os.path.join(output_dir, os.path.basename(input_file) + '.dcm')
    # Create DICOM file
    create_dicom_ecg(data, metadata, output_file)

def main():
    parser = argparse.ArgumentParser(description='Convert ECG data to DICOM format.')
    parser.add_argument('input', type=str, help='Path to the input ECG file (.hea or .xml) or directory')
    parser.add_argument('output_dir', type=str, help='Path to the output directory')
    parser.add_argument('-r', '--recursive', action='store_true', help='Process all files in the input directory')

    args = parser.parse_args()

    if args.recursive:
        if not os.path.isdir(args.input):
            print(f"Error: {args.input} is not a directory")
            return

        for root, _, files in os.walk(args.input):
            for file in files:
                if file.endswith('.hea') or file.endswith('.xml'):
                    input_file_path = os.path.join(root, file)
                    process_file(input_file_path, args.output_dir)
    else:
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file")
            return
        process_file(args.input, args.output_dir)

if __name__ == '__main__':
    main()
