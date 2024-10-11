import csv
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence
from datetime import datetime
import numpy as np
import uuid
import hashlib
import socket
import warnings

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


def generate_implementation_uid():
    # MAC-adress of computer
    mac_address = uuid.getnode()

    # Hostname of computer
    hostname = socket.gethostname()

    # Combination of data in a string
    unique_string = f"{mac_address}-{hostname}"
    # use one way function so that you cant get actual information of the system
    hash_object = hashlib.sha256(unique_string.encode())
    hex_dig = hash_object.hexdigest()
    numeric_hash = int(hex_dig, 16)
    numeric_hash_str = str(numeric_hash)
    # additional information loss (only 64 digits)
    implementation_uid = numeric_hash_str[:64]

    return implementation_uid

def create_file_meta():
    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 202
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.9.1.1" # ID = "12-lead ECG Waveform Storage" https://dicom.nema.org/dicom/2013/output/chtml/part04/sect_i.4.html
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_implementation_uid() # ID of the system which created the file
    return file_meta


def format_date(date_str):
    try:
        date_str = date_str.strip()

        # Try to parse as 'dd-mm-yyyy' format first
        try:
            return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y%m%d')
        except ValueError:
            pass

        # If that fails, try to parse as 'yyyy-mm-dd' format
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y%m%d')
        except ValueError:
            pass

        # If neither format works, return an empty string
        return ''

    except Exception as e:
        return ''

def format_time(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S').strftime('%H%M%S')
    except ValueError:
        return ''

def format_datetime(date_str, time_str):
    try:
        date = datetime.strptime(date_str, '%d-%m-%Y').date()
        time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
        return datetime.combine(date, time_obj).strftime('%Y%m%d%H%M%S')
    except ValueError:
        return ''

def add_patient_study_info(ds, metadata, file_meta, character_set='ISO_IR 192', procedure_code='P2-3120A', procedure_meaning='12 lead ECG'):
    ds.SpecificCharacterSet = character_set
    ds.InstanceCreationDate = datetime.now().strftime('%Y%m%d')
    ds.InstanceCreationTime = datetime.now().strftime('%H%M%S')
    ds.SOPClassUID = file_meta.get("MediaStorageSOPClassUID")
    ds.SOPInstanceUID = file_meta.get("MediaStorageSOPInstanceUID")
    ds.SeriesInstanceUID = str(pydicom.uid.generate_uid()).replace(".", "")
    ds.StudyInstanceUID = pydicom.uid.generate_uid()

    # Add study dates and times with warnings for missing metadata
    AdmitDate = metadata.get('AdmitDate', '')
    if not AdmitDate:
        warnings.warn("The tag 'AdmitDate' is not in the XML. Used instead the acquisition date. Used instead the acquisition date (ecg recording) for the DICOM Tag Study and Series date.")
    ds.StudyDate = format_date(AdmitDate)
    ds.SeriesDate = format_date(AdmitDate)

    AcquisitionDate = metadata.get('AcquisitionDate', '')
    if not AcquisitionDate:
        warnings.warn("The tag 'AcquisitionDate' is not in the XML")
    ds.ContentDate = format_date(AcquisitionDate)
    ds.AcquisitionDateTime = format_datetime(AcquisitionDate, metadata.get('AcquisitionTime', ''))

    AdmitTime = metadata.get('AdmitTime', '')
    if not AdmitTime:
        warnings.warn("The tag 'AdmitTime' is not in the XML. Used instead the acquisition time (ecg recording) for the DICOM Tag Study and Series time.")

    if AdmitTime:
        ds.StudyTime = format_time(AdmitTime)
    else:
        if not metadata.get('AcquisitionTime', ''):
            ds.StudyTime = metadata.get('AcquisitionTime', '')
    if AdmitTime:
        ds.SeriesTime = format_time(AdmitTime)
    else:
        if not metadata.get('AcquisitionTime', ''):
            ds.SeriesTime = metadata.get('AcquisitionTime', '')

    AcquisitionTime = metadata.get('AcquisitionTime', '')
    if not AcquisitionTime:
        warnings.warn("The tag 'AcquisitionTime' is not in the XML")
    ds.ContentTime = format_time(AcquisitionTime)

    # Rest of the metadata with warnings
    ds.AccessionNumber = ''
    ds.Modality = 'ECG'
    ds.Manufacturer = metadata.get('AcquisitionDevice', 'Unknown')
    if not metadata.get('AcquisitionDevice'):
        warnings.warn("The tag 'AcquisitionDevice' is not in the XML")

    ds.InstitutionName = metadata.get('SiteName', 'Unknown')
    if not metadata.get('SiteName'):
        warnings.warn("The tag 'SiteName' is not in the XML")

    ds.StudyDescription = 'RestingECG'
    ds.ProcedureCodeSequence = [Dataset()]
    ds.ProcedureCodeSequence[0].CodeValue = procedure_code
    ds.ProcedureCodeSequence[0].CodingSchemeDesignator = 'SRT'
    ds.ProcedureCodeSequence[0].CodeMeaning = procedure_meaning
    ds.SeriesDescription = 'RestingECG'

    ds.PatientID = metadata.get('PatientID', '')
    if not metadata.get('PatientID'):
        warnings.warn("The tag 'PatientID' is not in the XML")

    PatientAge = metadata.get('PatientAge')
    if not PatientAge:
        warnings.warn("The tag 'PatientAge' is not in the XML")
    ds.PatientAge = (PatientAge.zfill(3) + 'Y') if PatientAge else ''

    Sex = metadata.get('Gender', '')

    if not Sex:
        warnings.warn("The tag 'Gender' is not in the XML")
    else:
        if Sex.lower() == "male":
            Sex = 'M'
        if Sex.lower() == "female":
            Sex = 'F'
        if Sex.lower() == "other" or Sex.lower() == "non-binary":
            Sex = 'O'
        ds.PatientSex = Sex

    ds.PatientName = metadata.get('PatientName', 'Unknown^Patient')
    if not metadata.get('PatientName'):
        warnings.warn("The tags of the patient names are not in the XML")

    ds.PatientBirthDate = format_date(metadata.get('DateofBirth', ''))
    if not metadata.get('DateofBirth'):
        warnings.warn("The tag 'DateofBirth' is not in the XML")

    ds.PerformedProcedureStepStartDate = format_date(metadata.get('AcquisitionDate', ''))
    ds.PerformedProcedureStepStartTime = format_time(metadata.get('AcquisitionTime', ''))

    # Additional measurements (if needed)
    Measurements = metadata.get('Measurements', {})
    ds.add_new((0x0040, 0x0275), 'SQ', Sequence())
    item = Dataset()
    item.CodeValue = '8867-4'
    item.CodingSchemeDesignator = 'LN'
    item.CodeMeaning = 'Ventricular rate'
    item.MeasuredValueSequence = [Dataset()]
    item.MeasuredValueSequence[0].NumericValue = Measurements.get('VentricularRate', '')
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence = [Dataset()]
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeValue = 'uV'
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
    item.MeasuredValueSequence[0].CodeMeaning = 'microvolt'
    ds[0x0040, 0x0275].value.append(item)


def add_waveform_data(ds, data, metadata):
    lead_order = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    code_values = ['2:1', '2:2', '2:61', '2:62', '2:63', '2:64', '2:3', '2:4', '2:5', '2:6', '2:7', '2:8']
    num_samples = len(next(iter(data.values())))
    num_leads = len(lead_order)

    ds.is_little_endian = True
    ds.is_implicit_VR = False
    ds.WaveformSequence = Sequence()
    waveform_item = Dataset()
    waveform_item.MultiplexGroupTimeOffset = 0
    waveform_item.TriggerTimeOffset = 0
    waveform_item.WaveformOriginality = 'ORIGINAL'
    waveform_item.NumberOfWaveformChannels = num_leads
    waveform_item.NumberOfWaveformSamples = num_samples
    waveform_item.SamplingFrequency = metadata.get('SampleFrequency', '')
    waveform_item.WaveformBitsAllocated = 16
    waveform_item.WaveformSampleInterpretation = 'SS'
    waveform_data = np.zeros((num_samples, num_leads))
    waveform_item.ChannelDefinitionSequence = Sequence()

    for i, lead_id in enumerate(lead_order):
        channel_def_item = Dataset()
        channel_def_item.ChannelNumber = i + 1
        channel_def_item.ChannelLabel = f'Lead_{lead_id}'
        channel_def_item.ChannelStatus = 'OK'
        channel_def_item.WaveformBitsStored = 16
        channel_def_item.ChannelSourceSequence = Sequence([Dataset()])
        source = channel_def_item.ChannelSourceSequence[0]
        source.CodeValue = code_values[i]  # Set CodeValue based on the lead
        source.CodingSchemeDesignator = 'MDC'
        source.CodeMeaning = lead_id
        #channel_def_item.MeasurementUnitsCodeSequence = Sequence([Dataset()])
        #channel_def_item.MeasurementUnitsCodeSequence[0].CodeValue = 'uV'
        #channel_def_item.MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
        #channel_def_item.MeasurementUnitsCodeSequence[0].CodingSchemeVersion = '1.4'
        #channel_def_item.MeasurementUnitsCodeSequence[0].CodeMeaning = 'microvolt'

        lead_filters = metadata.get('LeadFilters', {})
        # Adding the channel-specific filter information
        channel_def_item.FilterLowFrequency = lead_filters.get(lead_id, {}).get('HighPassFilter', '0')
        channel_def_item.FilterHighFrequency = lead_filters.get(lead_id, {}).get('LowPassFilter', '0')
        channel_def_item.NotchFilterFrequency = lead_filters.get(lead_id, {}).get('ACFilter', '0')

        waveform_item.ChannelDefinitionSequence.append(channel_def_item)
        waveform_data[:, i] = data[lead_id] * 1000

    waveform_item.WaveformData = waveform_data.astype(np.int16).tobytes()
    ds.WaveformSequence.append(waveform_item)



def load_annotations_from_csv(csv_file):
    """Load annotations from a CSV file."""
    annotations = {}
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            measurement = row["measurement"]
            annotations[measurement] = {
                "code": row["code"],
                "description": row["description"],
                "unit": row["unit"],
                "unit_description": row["unit_description"],
                "scheme": row["scheme"],
                "scheme_version": row["scheme_version"],
            }
    return annotations

def merge_annotations(default_annotations, csv_annotations):
    """Merge CSV annotations with the default ones. CSV annotations override or add new measurements."""
    updated_annotations = default_annotations.copy()
    updated_annotations.update(csv_annotations)
    return updated_annotations

# Existing code for adding ECG data and annotations (unchanged)...

def create_dicom_ecg(data, metadata, output_file, annotations):
    ds = None
    file_meta = None

    # Handle file meta creation
    try:
        file_meta = create_file_meta()
    except Exception as e:
        raise RuntimeError(f"Error creating file meta information: {str(e)}")

    # Create the DICOM file dataset
    try:
        ds = FileDataset(output_file, {}, file_meta=file_meta, preamble=b"\0" * 128)
    except Exception as e:
        raise RuntimeError(f"Error creating DICOM dataset: {str(e)}")

    # Add patient and study info
    try:
        add_patient_study_info(ds, metadata, file_meta)
    except KeyError as e:
        raise RuntimeError(f"Missing required patient or study metadata: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error adding patient/study info: {str(e)}")

    # Add waveform data
    try:
        add_waveform_data(ds, data, metadata)
    except KeyError as e:
        raise RuntimeError(f"Missing required waveform data: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error adding waveform data: {str(e)}")

    # Add acquisition context
    try:
        add_acquisition_context_sequence(ds, metadata)
    except Exception as e:
        raise RuntimeError(f"Error adding acquisition context sequence: {str(e)}")

    # Add annotations
    try:
        add_annotations(ds, metadata, annotations)
    except KeyError as e:
        raise RuntimeError(f"Missing required annotation data: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error adding annotations: {str(e)}")

    # Save the DICOM file
    try:
        ds.save_as(output_file)
        print(f'DICOM file saved as {output_file}')
    except Exception as e:
        raise RuntimeError(f"Error saving DICOM file: {str(e)}")


def add_annotations(ds, metadata, annotations):
    ds.WaveformAnnotationSequence = Sequence()
    measurements = metadata.get('measurements', {})

    for diagnosis in metadata.get('diagnosis', []):
        annotation_item = Dataset()
        annotation_item.ReferencedWaveformChannels = 0
        annotation_item.AnnotationGroupNumber = 0
        annotation_item.UnformattedTextValue = diagnosis
        ds.WaveformAnnotationSequence.append(annotation_item)

    if metadata.get('RRInterval'):
        annotation_rrinterval = annotations["RRInterval"]
        create_ecg_annotation(
            ds,
            1,  # Annotation group number
            metadata.get('RRInterval'),
            annotation_rrinterval["code"],
            annotation_rrinterval["description"],
            annotation_rrinterval["unit"],
            annotation_rrinterval["unit_description"],
            annotation_rrinterval["scheme"],
            annotation_rrinterval["scheme_version"]
        )

    for measurement, annotation in annotations.items():
        if measurement in measurements:
            create_ecg_annotation(
                ds,
                1,  # Annotation group number
                measurements[measurement],
                annotation["code"],
                annotation["description"],
                annotation["unit"],
                annotation["unit_description"],
                annotation["scheme"],
                annotation["scheme_version"]
            )

def create_ecg_annotation(ds, annotation_group_number, value, code_value, code_meaning, unit_code_value,
                          unit_code_meaning, codingschemedesignator, codeschemeversion):
    annotation_item = Dataset()
    annotation_item.AnnotationGroupNumber = annotation_group_number
    annotation_item.NumericValue = pydicom.valuerep.DSfloat(value)

    # Define the Measurement Units Code Sequence using the provided units
    mu_item = Dataset()
    mu_item.CodeValue = unit_code_value
    mu_item.CodingSchemeDesignator = 'UCUM'
    mu_item.CodingSchemeVersion = "1.4"
    mu_item.CodeMeaning = unit_code_meaning
    annotation_item.MeasurementUnitsCodeSequence = Sequence([mu_item])

    # Define the Concept Name Code Sequence with MDC information
    conceptnamecodesequence = Dataset()
    conceptnamecodesequence.CodeValue = code_value
    conceptnamecodesequence.CodingSchemeDesignator = codingschemedesignator
    conceptnamecodesequence.CodingSchemeVersion = codeschemeversion
    conceptnamecodesequence.CodeMeaning = code_meaning
    annotation_item.ConceptNameCodeSequence = Sequence([conceptnamecodesequence])

    ds.WaveformAnnotationSequence.append(annotation_item)
def create_ecg_annotation(ds, annotation_group_number, value, code_value, code_meaning, unit_code_value,
                          unit_code_meaning, codingschemedesignator, codeschemeversion):
    annotation_item = Dataset()
    # Reference the correct waveform channels
    annotation_item.ReferencedWaveformChannels = 0
    annotation_item.AnnotationGroupNumber = annotation_group_number
    # Set the numeric value for the interval
    annotation_item.NumericValue = pydicom.valuerep.DSfloat(value)

    # Define the Measurement Units Code Sequence using the provided units
    mu_item = Dataset()
    mu_item.CodeValue = unit_code_value  # Measurement unit code, e.g., 'ms', '{H.B.}/min', 'deg'
    mu_item.CodingSchemeDesignator = 'UCUM'
    mu_item.CodingSchemeVersion = "1.4"
    mu_item.CodeMeaning = unit_code_meaning  # The meaning, e.g., 'millisecond', 'heart beats per minute', 'degrees'
    annotation_item.MeasurementUnitsCodeSequence = Sequence([mu_item])

    # Define the Concept Name Code Sequence with MDC information
    conceptnamecodesequence = Dataset()
    conceptnamecodesequence.CodeValue = code_value  # The specific MDC code
    conceptnamecodesequence.CodingSchemeDesignator = codingschemedesignator
    conceptnamecodesequence.CodingSchemeVersion = codeschemeversion
    conceptnamecodesequence.CodeMeaning = code_meaning  # Description of the interval
    annotation_item.ConceptNameCodeSequence = Sequence([conceptnamecodesequence])

    # Append to the dataset
    ds.WaveformAnnotationSequence.append(annotation_item)


def add_acquisition_context_sequence(ds, metadata):
    # Create the Acquisition Context Sequence
    acq_context_seq = Sequence()

    # First item (Lead System)
    item1 = Dataset()
    item1.ValueType = 'CODE'

    # ConceptNameCodeSequence for Lead System
    item1.ConceptNameCodeSequence = Sequence([Dataset()])
    item1.ConceptNameCodeSequence[0].CodeValue = '10:11345'
    item1.ConceptNameCodeSequence[0].CodingSchemeDesignator = 'MDC'
    item1.ConceptNameCodeSequence[0].CodeMeaning = 'Lead System'

    # Concept Code Sequence for Standard 12-lead
    item1.ConceptCodeSequence = Sequence([Dataset()])
    item1.ConceptCodeSequence[0].CodeValue = '10:11265'
    item1.ConceptCodeSequence[0].CodingSchemeDesignator = 'MDC'
    item1.ConceptCodeSequence[0].CodeMeaning = 'Standard 12-lead'

    # Append the first item (Lead System) to the sequence
    acq_context_seq.append(item1)

    # Second item (Heart Rate)
    item2 = Dataset()
    item2.ValueType = 'NUMERIC'

    # ConceptNameCodeSequence for Heart Rate
    item2.ConceptNameCodeSequence = Sequence([Dataset()])
    item2.ConceptNameCodeSequence[0].CodeValue = '8867-4'
    item2.ConceptNameCodeSequence[0].CodingSchemeDesignator = 'LN'
    item2.ConceptNameCodeSequence[0].CodingSchemeVersion = '19971101'
    item2.ConceptNameCodeSequence[0].CodeMeaning = 'Heart rate'

    # Measurement Units Code Sequence for Heart Rate
    item2.MeasurementUnitsCodeSequence = Sequence([Dataset()])
    item2.MeasurementUnitsCodeSequence[0].CodeValue = '{H.B.}/min'
    item2.MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
    item2.MeasurementUnitsCodeSequence[0].CodingSchemeVersion = '1.4'
    item2.MeasurementUnitsCodeSequence[0].CodeMeaning = 'Heart beat per minute'

    # Set the heart rate value from metadata
    ventricular_rate = metadata.get('measurements').get('ventricular_rate', None)
    if ventricular_rate:
        item2.NumericValue = pydicom.valuerep.DSfloat(ventricular_rate)

    # Append the second item (Heart Rate) to the sequence
    acq_context_seq.append(item2)

    # Add the sequence to the dataset
    ds.AcquisitionContextSequence = acq_context_seq
