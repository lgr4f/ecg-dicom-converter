import argparse
from .extract_ecg_and_metadata import extract_data
from .load_to_dicom import create_dicom_ecg

def main():
    parser = argparse.ArgumentParser(description='Convert ECG data to DICOM format.')
    parser.add_argument('input_file', type=str, help='Path to the input ECG file (.hea or .xml)')
    parser.add_argument('output_file', type=str, help='Path to the output DICOM file')

    args = parser.parse_args()

    # Extract ECG data and metadata
    data, metadata = extract_data(args.input_file)

    # Create DICOM file
    create_dicom_ecg(data, metadata, args.output_file)

if __name__ == '__main__':
    main()
