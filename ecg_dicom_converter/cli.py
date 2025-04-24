import argparse
import os
from ecg_dicom_converter.extract_ecg_and_metadata import extract_data
from ecg_dicom_converter.load_to_dicom import create_dicom_ecg, DEFAULT_ANNOTATIONS, load_annotations_from_csv, merge_annotations

class AnnotationsFileNotFoundError(Exception):
    pass

def process_file(input_file, output_dir, annotations):
    try:
        # Extract ECG data and metadata
        rhythm_leads, median_leads, metadata = extract_data(input_file)

        # Create output file path
        output_file = os.path.join(output_dir, remove_all_extensions(os.path.basename(input_file)) + '.dcm')

        # Create DICOM file
        create_dicom_ecg(rhythm_leads, median_leads, metadata, output_file, annotations)

    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        raise
def remove_all_extensions(filename):
    while True:
        filename, ext = os.path.splitext(filename)
        if ext == '':
            return filename
def main():
    parser = argparse.ArgumentParser(description='Convert ECG data to DICOM format.')
    parser.add_argument('input', type=str, help='Path to the input ECG file (.xml) or directory')
    parser.add_argument('output_dir', type=str, help='Path to the output directory')
    parser.add_argument('--annotations', type=str, help='Path to the annotations CSV file', default=None)
    parser.add_argument('-r', '--recursive', action='store_true', help='Process all files in the input directory')

    args = parser.parse_args()

    # Load default annotations
    annotations = DEFAULT_ANNOTATIONS.copy()

    # If a CSV file is provided, load it and update the default annotations
    if args.annotations:
        try:
            csv_annotations = load_annotations_from_csv(args.annotations)
            annotations = merge_annotations(annotations, csv_annotations)
        except FileNotFoundError:
            print(f"Error: Provided annotations CSV file not found: {args.annotations}")
            return

    if args.recursive:
        if not os.path.isdir(args.input):
            print(f"Error: {args.input} is not a directory")
            return

        for root, _, files in os.walk(args.input):
            for file in files:
                if file.endswith('.xml'):
                    input_file_path = os.path.join(root, file)
                    try:
                        process_file(input_file_path, args.output_dir, annotations)
                    except Exception:
                        print(f"Skipping file {input_file_path} due to error.")
    else:
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file")
            return
        try:
            process_file(args.input, args.output_dir, annotations)
        except Exception:
            print(f"Skipping file {args.input} due to error.")

if __name__ == '__main__':
    main()
