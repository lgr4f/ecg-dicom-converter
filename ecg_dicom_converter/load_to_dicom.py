import csv
from pydicom import uid, valuerep, dataset, sequence
from datetime import datetime, timedelta
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
    file_meta = dataset.FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 202
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.9.1.1" # ID = "12-lead ECG Waveform Storage" https://dicom.nema.org/dicom/2013/output/chtml/part04/sect_i.4.html
    file_meta.MediaStorageSOPInstanceUID = uid.generate_uid()
    file_meta.TransferSyntaxUID = uid.ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = generate_implementation_uid() # ID of the system which created the file
    return file_meta


def format_date(date_str):
    try:
        date_str = date_str.strip()

        # Try to parse as 'dd-mm-yyyy' format first
        try:
            return datetime.strptime(date_str, '%m-%d-%Y').strftime('%Y%m%d')
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
    date_formats = ['%d-%m-%Y', '%m-%d-%Y',  '%Y-%m-%d', '%Y%m%d']
    time_formats = ['%H:%M:%S', '%H%M%S']

    for df in date_formats:
        try:
            date = datetime.strptime(date_str, df).date()
            break
        except (ValueError, TypeError):
            continue
    else:
        return ''

    for tf in time_formats:
        try:
            time_obj = datetime.strptime(time_str, tf).time()
            break
        except (ValueError, TypeError):
            continue
    else:
        return ''

    return datetime.combine(date, time_obj).strftime('%Y%m%d%H%M%S')


def add_patient_study_info(ds, metadata, file_meta, character_set='ISO_IR 192', procedure_code='P2-3120A', procedure_meaning='12 lead ECG'):
    # Grundlegende DICOM-Felder setzen
    now = datetime.now()
    ds.SpecificCharacterSet = character_set
    ds.InstanceCreationDate = now.strftime('%Y%m%d')
    ds.InstanceCreationTime = now.strftime('%H%M%S')
    ds.SOPClassUID = file_meta.get("MediaStorageSOPClassUID")
    ds.SOPInstanceUID = file_meta.get("MediaStorageSOPInstanceUID")
    ds.SeriesInstanceUID = str(uid.generate_uid()).replace(".", "")
    ds.StudyInstanceUID = uid.generate_uid()

    # Datum & Uhrzeit auslesen
    admit_date = metadata.get('AdmitDate')
    admit_time = metadata.get('AdmitTime')
    acquisition_date = metadata.get('AcquisitionDate')
    acquisition_time = metadata.get('AcquisitionTime')

    # ContentDate und ContentTime
    ds.ContentDate = format_date(acquisition_date)
    ds.ContentTime = format_time(acquisition_time)

    # AcquisitionDateTime
    ds.AcquisitionDateTime = format_datetime(acquisition_date, acquisition_time)
    if not acquisition_date or not acquisition_time:
        warnings.warn("Incomplete or missing 'AcquisitionDate'/'AcquisitionTime'. 'AcquisitionDateTime' may be incomplete.")

    # StudyDate / SeriesDate
    if admit_date:
        ds.StudyDate = format_date(admit_date)
        ds.SeriesDate = format_date(admit_date)
    elif acquisition_date:
        warnings.warn("'AdmitDate' missing. Using 'AcquisitionDate' instead for Study/Series Date.")
        ds.StudyDate = format_date(acquisition_date)
        ds.SeriesDate = format_date(acquisition_date)
    else:
        warnings.warn("Neither 'AdmitDate' nor 'AcquisitionDate' available. Cannot set Study/Series Date.")

    # StudyTime / SeriesTime
    if admit_time:
        ds.StudyTime = format_time(admit_time)
        ds.SeriesTime = format_time(admit_time)
    elif acquisition_time:
        warnings.warn("'AdmitTime' missing. Using 'AcquisitionTime' instead for Study/Series Time.")
        ds.StudyTime = format_time(acquisition_time)
        ds.SeriesTime = format_time(acquisition_time)
    else:
        warnings.warn("Neither 'AdmitTime' nor 'AcquisitionTime' available. Cannot set Study/Series Time.")

    # Rest of the metadata with warnings
    ds.AccessionNumber = ''
    ds.Modality = 'ECG'
    ds.Manufacturer = "GE HealthCare"
    ds.ManufacturerModelName = metadata.get('AcquisitionDevice', 'Unknown')
    ds.StationName = metadata.get('LocationName', 'Unknown')
    if not metadata.get('AcquisitionDevice'):
        warnings.warn("The tag 'AcquisitionDevice' is not in the XML")

    ds.InstitutionName = metadata.get('SiteName', 'Unknown')
    if not metadata.get('SiteName'):
        warnings.warn("The tag 'SiteName' is not in the XML")

    ds.StudyDescription = 'RestingECG'
    ds.ProcedureCodeSequence = [dataset.Dataset()]
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
    ds.PerformedProcedureStepEndDate = str(get_performed_procedure_step_end_data(metadata)[0])
    ds.PerformedProcedureStepEndTime = str(get_performed_procedure_step_end_data(metadata)[1])

    # Additional measurements (if needed)
    Measurements = metadata.get('Measurements', {})
    ds.add_new((0x0040, 0x0275), 'SQ', sequence.Sequence())
    item = dataset.Dataset()
    item.CodeValue = '8867-4'
    item.CodingSchemeDesignator = 'LN'
    item.CodeMeaning = 'Ventricular rate'
    item.MeasuredValueSequence = [dataset.Dataset()]
    item.MeasuredValueSequence[0].NumericValue = Measurements.get('VentricularRate', '')
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence = [dataset.Dataset()]
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeValue = 'uV'
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
    item.MeasuredValueSequence[0].CodeMeaning = 'microvolt'
    ds[0x0040, 0x0275].value.append(item)

def get_performed_procedure_step_end_data(metadata):
    max_sample_count = max(metadata['RhythmCount'].values())
    sampling_frequency = metadata['SampleFrequency']

    # Startzeit und Datum auslesen
    acquisition_time = metadata['AcquisitionTime']  # Erwartetes Format: HHMMSS
    acquisition_date = metadata['AcquisitionDate']  # Erwartetes Format: YYYYMMDD

    # Falls das Format nicht korrekt ist, umwandeln
    if "-" in acquisition_date:  # Prüfen auf abweichendes Format
        acquisition_date = datetime.strptime(acquisition_date, "%m-%d-%Y").strftime("%Y%m%d")
    if ":" in acquisition_time:  # Prüfen auf abweichendes Format
        acquisition_time = acquisition_time.replace(":", "")

    # Startzeitpunkt als datetime-Objekt erstellen
    start_datetime = datetime.strptime(f"{acquisition_date}{acquisition_time}", "%Y%m%d%H%M%S")

    # Dauer in Sekunden berechnen und zur Startzeit hinzufügen
    duration_seconds = max_sample_count / sampling_frequency
    end_datetime = start_datetime + timedelta(seconds=duration_seconds)

    # Enddatum und -zeit formatieren
    end_date = end_datetime.strftime("%Y%m%d")
    end_time = end_datetime.strftime("%H%M%S")

    return end_date, end_time


def get_performed_procedure_step_end_time(metadata):
    max_sample_count_key = max(metadata['SampleCount'].values())
    sampling_frequency = metadata['SampleFrequency']
    start_time = metadata['AcquisitionTime']

def add_waveform_data(ds, waveform_dict, metadata):
    """
    Add both rhythm and median waveform data to the DICOM file.
    waveform_dict should be like:
        {
            "Rhythm": {...},
            "Median": {...}
        }
    """
    ds.WaveformSequence = sequence.Sequence()

    lead_order = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    code_values = ['2:1', '2:2', '2:61', '2:62', '2:63', '2:64', '2:3', '2:4', '2:5', '2:6', '2:7', '2:8']

    for label in ["Rhythm", "Median"]:
        if label not in waveform_dict or not waveform_dict[label]:
            continue  # Skip if missing

        data = waveform_dict[label]
        num_samples = len(next(iter(data.values())))
        num_leads = len(lead_order)

        waveform_item = dataset.Dataset()
        waveform_item.MultiplexGroupTimeOffset = 0
        waveform_item.MultiplexGroupLabel = label.upper()
        waveform_item.TriggerTimeOffset = 0
        waveform_item.WaveformOriginality = 'ORIGINAL'
        waveform_item.NumberOfWaveformChannels = num_leads
        waveform_item.NumberOfWaveformSamples = num_samples
        waveform_item.SamplingFrequency = metadata.get('SampleFrequency', '')
        waveform_item.WaveformBitsAllocated = 16
        waveform_item.WaveformSampleInterpretation = 'SS'
        waveform_data = np.zeros((num_samples, num_leads))
        waveform_item.ChannelDefinitionSequence = sequence.Sequence()

        lead_filters = metadata.get(f'{label}LeadFilters', {})

        for i, lead_id in enumerate(lead_order):
            channel_def_item = dataset.Dataset()
            channel_def_item.ChannelNumber = i + 1
            channel_def_item.ChannelLabel = f'Lead_{lead_id}'
            channel_def_item.ChannelStatus = 'OK'
            channel_def_item.WaveformBitsStored = 16
            channel_def_item.ChannelSourceSequence = sequence.Sequence([dataset.Dataset()])
            source = channel_def_item.ChannelSourceSequence[0]
            source.CodeValue = code_values[i]
            source.CodingSchemeDesignator = 'MDC'
            source.CodeMeaning = lead_id
            channel_def_item.ChannelSensitivityUnitsSequence = sequence.Sequence([dataset.Dataset()])
            channel_def_item.ChannelSensitivityUnitsSequence[0].CodeValue = 'uV'
            channel_def_item.ChannelSensitivityUnitsSequence[0].CodingSchemeDesignator = 'UCUM'
            channel_def_item.ChannelSensitivityUnitsSequence[0].CodingSchemeVersion = '1.4'
            channel_def_item.ChannelSensitivityUnitsSequence[0].CodeMeaning = 'microvolt'

            # Add filter info
            channel_def_item.FilterLowFrequency = lead_filters.get(lead_id, {}).get('HighPassFilter', '0')
            channel_def_item.FilterHighFrequency = lead_filters.get(lead_id, {}).get('LowPassFilter', '0')
            channel_def_item.NotchFilterFrequency = lead_filters.get(lead_id, {}).get('ACFilter', '0')

            waveform_item.ChannelDefinitionSequence.append(channel_def_item)

            if lead_id in data:
                waveform_data[:, i] = data[lead_id] * 1000  # uV to mV
            else:
                waveform_data[:, i] = 0  # Fill with zeros if lead missing

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

def create_dicom_ecg(rhythm_leads, median_leads, metadata, output_file, annotations):
    ds = None
    file_meta = None

    # Handle file meta creation
    try:
        file_meta = create_file_meta()
    except Exception as e:
        raise RuntimeError(f"Error creating file meta information: {str(e)}")

    # Create the DICOM file dataset
    try:
        ds = dataset.FileDataset(output_file, {}, file_meta=file_meta, preamble=b"\0" * 128)
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
        add_waveform_data(ds, {
            "Rhythm": rhythm_leads,
            "Median": median_leads
        }, metadata)

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
        ds.save_as(output_file, little_endian=True, implicit_vr=False)
        print(f'DICOM file saved as {output_file}')
    except Exception as e:
        raise RuntimeError(f"Error saving DICOM file: {str(e)}")


def add_annotations(ds, metadata, annotations):
    ds.WaveformAnnotationSequence = sequence.Sequence()
    measurements = metadata.get('measurements', {})

    for diagnosis in metadata.get('diagnosis', []):
        annotation_item = dataset.Dataset()
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
    annotation_item = dataset.Dataset()
    annotation_item.AnnotationGroupNumber = annotation_group_number
    annotation_item.NumericValue = valuerep.DSfloat(value)

    # Define the Measurement Units Code Sequence using the provided units
    mu_item = dataset.Dataset()
    mu_item.CodeValue = unit_code_value
    mu_item.CodingSchemeDesignator = 'UCUM'
    mu_item.CodingSchemeVersion = "1.4"
    mu_item.CodeMeaning = unit_code_meaning
    annotation_item.MeasurementUnitsCodeSequence = Sequence([mu_item])

    # Define the Concept Name Code Sequence with MDC information
    conceptnamecodesequence = dataset.Dataset()
    conceptnamecodesequence.CodeValue = code_value
    conceptnamecodesequence.CodingSchemeDesignator = codingschemedesignator
    conceptnamecodesequence.CodingSchemeVersion = codeschemeversion
    conceptnamecodesequence.CodeMeaning = code_meaning
    annotation_item.ConceptNameCodeSequence = Sequence([conceptnamecodesequence])

    ds.WaveformAnnotationSequence.append(annotation_item)
def create_ecg_annotation(ds, annotation_group_number, value, code_value, code_meaning, unit_code_value,
                          unit_code_meaning, codingschemedesignator, codeschemeversion):
    annotation_item = dataset.Dataset()
    # Reference the correct waveform channels
    annotation_item.ReferencedWaveformChannels = 0
    annotation_item.AnnotationGroupNumber = annotation_group_number
    # Set the numeric value for the interval
    annotation_item.NumericValue = valuerep.DSfloat(value)

    # Define the Measurement Units Code Sequence using the provided units
    mu_item = dataset.Dataset()
    mu_item.CodeValue = unit_code_value  # Measurement unit code, e.g., 'ms', '{H.B.}/min', 'deg'
    mu_item.CodingSchemeDesignator = 'UCUM'
    mu_item.CodingSchemeVersion = "1.4"
    mu_item.CodeMeaning = unit_code_meaning  # The meaning, e.g., 'millisecond', 'heart beats per minute', 'degrees'
    annotation_item.MeasurementUnitsCodeSequence = sequence.Sequence([mu_item])

    # Define the Concept Name Code Sequence with MDC information
    conceptnamecodesequence = dataset.Dataset()
    conceptnamecodesequence.CodeValue = code_value  # The specific MDC code
    conceptnamecodesequence.CodingSchemeDesignator = codingschemedesignator
    conceptnamecodesequence.CodingSchemeVersion = codeschemeversion
    conceptnamecodesequence.CodeMeaning = code_meaning  # Description of the interval
    annotation_item.ConceptNameCodeSequence = sequence.Sequence([conceptnamecodesequence])

    # Append to the dataset
    ds.WaveformAnnotationSequence.append(annotation_item)


def add_acquisition_context_sequence(ds, metadata):
    # Create the Acquisition Context Sequence
    acq_context_seq = sequence.Sequence()

    # First item (Lead System)
    item1 = dataset.Dataset()
    item1.ValueType = 'CODE'

    # ConceptNameCodeSequence for Lead System
    item1.ConceptNameCodeSequence = sequence.Sequence([dataset.Dataset()])
    item1.ConceptNameCodeSequence[0].CodeValue = '10:11345'
    item1.ConceptNameCodeSequence[0].CodingSchemeDesignator = 'MDC'
    item1.ConceptNameCodeSequence[0].CodeMeaning = 'Lead System'

    # Concept Code Sequence for Standard 12-lead
    item1.ConceptCodeSequence = sequence.Sequence([dataset.Dataset()])
    item1.ConceptCodeSequence[0].CodeValue = '10:11265'
    item1.ConceptCodeSequence[0].CodingSchemeDesignator = 'MDC'
    item1.ConceptCodeSequence[0].CodeMeaning = 'Standard 12-lead'

    # Append the first item (Lead System) to the sequence
    acq_context_seq.append(item1)

    # Second item (Heart Rate)
    item2 = dataset.Dataset()
    item2.ValueType = 'NUMERIC'

    # ConceptNameCodeSequence for Heart Rate
    item2.ConceptNameCodeSequence = sequence.Sequence([dataset.Dataset()])
    item2.ConceptNameCodeSequence[0].CodeValue = '8867-4'
    item2.ConceptNameCodeSequence[0].CodingSchemeDesignator = 'LN'
    item2.ConceptNameCodeSequence[0].CodingSchemeVersion = '19971101'
    item2.ConceptNameCodeSequence[0].CodeMeaning = 'Heart rate'

    # Measurement Units Code Sequence for Heart Rate
    item2.MeasurementUnitsCodeSequence = sequence.Sequence([dataset.Dataset()])
    item2.MeasurementUnitsCodeSequence[0].CodeValue = '{H.B.}/min'
    item2.MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
    item2.MeasurementUnitsCodeSequence[0].CodingSchemeVersion = '1.4'
    item2.MeasurementUnitsCodeSequence[0].CodeMeaning = 'Heart beat per minute'

    # Set the heart rate value from metadata
    ventricular_rate = metadata.get('measurements').get('ventricular_rate', None)
    if ventricular_rate:
        item2.NumericValue = valuerep.DSfloat(ventricular_rate)

    # Append the second item (Heart Rate) to the sequence
    acq_context_seq.append(item2)

    # Add the sequence to the dataset
    ds.AcquisitionContextSequence = acq_context_seq
