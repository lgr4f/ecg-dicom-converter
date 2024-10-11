from scripts import extract_ecg_and_metadata
from scripts import load_to_dicom
from scripts import validate_dicom
# Default annotations (from the current `annotations.csv`)
DEFAULT_ANNOTATIONS = {
    "PRInterval": {
        "code": "2:15872",
        "description": "PR interval global",
        "unit": "ms",
        "unit_description": "millisecond",
        "scheme": "MDC",
        "scheme_version": "20080927"
    },
    "QTInterval": {
        "code": "2:16160",
        "description": "QT interval global",
        "unit": "ms",
        "unit_description": "millisecond",
        "scheme": "MDC",
        "scheme_version": "20080927"
    },
    "QRSDuration": {
        "code": "2:16156",
        "description": "QRS duration global",
        "unit": "ms",
        "unit_description": "millisecond",
        "scheme": "MDC",
        "scheme_version": "20080927"
    },
    "RRInterval": {
        "code": "2:16168",
        "description": "RR interval global",
        "unit": "ms",
        "unit_description": "millisecond",
        "scheme": "MDC",
        "scheme_version": "20080927"
    },
    "VentricularRate": {
        "code": "8867-4",
        "description": "Heart rate",
        "unit": "{H.B.}/min",
        "unit_description": "Heart beat per minute",
        "scheme": "LN",
        "scheme_version": "19971101"
    },
    "PAxis": {
        "code": "8626-4",
        "description": "P wave axis",
        "unit": "deg",
        "unit_description": "degree",
        "scheme": "LN",
        "scheme_version": "19971101"
    },
    "RAxis": {
        "code": "9997-8",
        "description": "R wave axis",
        "unit": "deg",
        "unit_description": "degree",
        "scheme": "LN",
        "scheme_version": "19971101"
    },
    "TAxis": {
        "code": "8638-9",
        "description": "T wave axis",
        "unit": "deg",
        "unit_description": "degree",
        "scheme": "LN",
        "scheme_version": "19971101"
    },
    "QOnset": {
        "code": "5.10.3-3",
        "description": "Q Onset",
        "unit": "POINT",
        "unit_description": "POINT",
        "scheme": "SCPECG",
        "scheme_version": "1.3"
    },
    "POnset": {
        "code": "5.10.3-1",
        "description": "P Onset",
        "unit": "POINT",
        "unit_description": "POINT",
        "scheme": "SCPECG",
        "scheme_version": "1.3"
    },
    "QOffset": {
        "code": "5.10.3-4",
        "description": "Q Offset",
        "unit": "POINT",
        "unit_description": "POINT",
        "scheme": "SCPECG",
        "scheme_version": "1.3"
    },
    "POffset": {
        "code": "5.10.3-2",
        "description": "P Offset",
        "unit": "POINT",
        "unit_description": "POINT",
        "scheme": "SCPECG",
        "scheme_version": "1.3"
    }
}


file_path = 'C:/Users/graf35/Desktop/Coding/ecg-uploader/data/xml/hannover_demo.xml'
output = 'C:/Users/graf35/Desktop/Coding/ecg-uploader/data/dicom/test2.dcm'
csv_annotations_path = "./annotations.csv"
ecgdata, metadata = extract_ecg_and_metadata.extract_data(file_path)
output_file_path = load_to_dicom.create_dicom_ecg(ecgdata, metadata, output, DEFAULT_ANNOTATIONS)
if output_file_path:
    validate_dicom.read_file(output_file_path)
pass