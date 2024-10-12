import argparse
import os
import csv
from .extract_ecg_and_metadata import extract_data
from .load_to_dicom import create_dicom_ecg, DEFAULT_ANNOTATIONS, load_annotations_from_csv, merge_annotations
from .validate_dicom import validate_dicom_file
import time
class AnnotationsFileNotFoundError(Exception):
    pass

def process_file(input_file, output_dir, annotations, pseudonym_number_file):
    try:
        # Create output file path
        output_file = os.path.join(output_dir, os.path.basename(input_file) + '.dcm')
        # Extract ECG data and metadata
        data, metadata, xml_filesize = extract_data(input_file, pseudonym_number_file+"_xml")
        # Create DICOM file
        output_file_path, dicom_filesize = create_dicom_ecg(data, metadata, output_file, annotations, pseudonym_number_file+"_dicom")
        return xml_filesize, output_file_path, dicom_filesize

    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Convert ECG data to DICOM format.')
    parser.add_argument('input', type=str, help='Path to the input ECG file (.hea or .xml) or directory')
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

        pseudonym_number_file = 1
        for root, _, files in os.walk(args.input):
            for file in files:
                if file.endswith('.hea') or file.endswith('.xml'):
                    input_file_path = os.path.join(root, file)
                    performance_log_path = os.path.join(os.path.dirname(input_file_path), '../performance.csv')
                    try:
                        start_time = time.time()
                        xml_filesize, output_file_path, dicom_filesize = process_file(input_file_path, args.output_dir, annotations, str(pseudonym_number_file))
                        elapsed_time = (time.time() - start_time) * 1000  # Time in milliseconds
                        elapsed_time = str(elapsed_time).replace('.', ',')
                        log_performance(performance_log_path, str(pseudonym_number_file)+"_overall", elapsed_time, xml_filesize, dicom_filesize)
                        validate_dicom_file(output_file_path, str(pseudonym_number_file)+"_validation")
                        pseudonym_number_file = pseudonym_number_file + 1
                    except Exception:
                        print(f"Skipping file {input_file_path} due to error.")
                        log_performance(performance_log_path,str(pseudonym_number_file)+"_overall", "-", "-",
                                        "Fehlgeschlagen")
    else:
        if not os.path.isfile(args.input):
            print(f"Error: {args.input} is not a valid file")
            return
        try:
            process_file(args.input, args.output_dir, annotations)
        except Exception:
            print(f"Skipping file {args.input} due to error.")


def log_performance(performance_log_path, filename, overall_time, xml_filesize, dicom_filesize):
    """Helper function to log performance to the CSV file, creating it with headers if necessary."""

    file_exists = os.path.isfile(performance_log_path)

    with open(performance_log_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=';')

        # Write headers if the file doesn't exist
        if not file_exists:
            writer.writerow(["Filename (pseudonym)", "Overall time", "XML file size", "DICOM file size"])

        # Write the performance data
        writer.writerow([filename, overall_time, xml_filesize, dicom_filesize])

if __name__ == '__main__':
    main()
