import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence
from datetime import datetime
import numpy as np
import os

def create_file_meta():
    file_meta = pydicom.dataset.FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 202
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = pydicom.uid.generate_uid()
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    file_meta.ImplementationClassUID = pydicom.uid.generate_uid()
    return file_meta

def format_date(date_str):
    try:
        return datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y%m%d')
    except ValueError:
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

def add_patient_study_info(ds, metadata, character_set='ISO_IR 192', procedure_code='P2-3120A', procedure_meaning='12 lead ECG'):
    ds.SpecificCharacterSet = character_set
    ds.InstanceCreationDate = datetime.now().strftime('%Y%m%d')
    ds.InstanceCreationTime = datetime.now().strftime('%H%M%S')
    ds.SOPClassUID = pydicom.uid.generate_uid()
    ds.SOPInstanceUID = pydicom.uid.generate_uid()
    ds.SeriesInstanceUID = "1"
    ds.StudyDate = format_date(metadata.get('admit_date', ''))
    ds.SeriesDate = format_date(metadata.get('admit_date', ''))
    ds.ContentDate = format_date(metadata.get('acquisition_date', ''))
    ds.AcquisitionDateTime = format_datetime(metadata.get('acquisition_date', ''), metadata.get('acquisition_time', ''))
    ds.StudyTime = format_time(metadata.get('admit_time', ''))
    ds.SeriesTime = format_time(metadata.get('admit_time', ''))
    ds.ContentTime = format_time(metadata.get('acquisition_time', ''))
    ds.AccessionNumber = ''
    ds.Modality = 'ECG'
    ds.Manufacturer = metadata.get('device', 'Unknown')
    ds.InstitutionName = metadata.get('site', 'Unknown')
    ds.StudyDescription = 'RestingECG'
    ds.ProcedureCodeSequence = [Dataset()]
    ds.ProcedureCodeSequence[0].CodeValue = procedure_code
    ds.ProcedureCodeSequence[0].CodingSchemeDesignator = 'SRT'
    ds.ProcedureCodeSequence[0].CodeMeaning = procedure_meaning
    ds.SeriesDescription = 'RestingECG'
    ds.PatientID = metadata.get('patient_id', '')
    ds.PatientAge = metadata.get('patient_age', '').zfill(3) + 'Y'
    ds.PatientSex = metadata.get('patient_sex', '')
    ds.PatientName = metadata.get('patient_name', 'Unknown^Patient')
    ds.PatientBirthDate = format_date(metadata.get('patient_birthdate', ''))
    ds.EthnicGroup = 'Undefined'
    ds.PerformedProcedureStepStartDate = format_date(metadata.get('admit_date', ''))
    ds.PerformedProcedureStepStartTime = format_time(metadata.get('admit_time', ''))

    # Additional measurements (if needed)
    measurements = metadata.get('measurements', {})
    ds.add_new((0x0040, 0x0275), 'SQ', Sequence())
    item = Dataset()
    item.CodeValue = '8867-4'
    item.CodingSchemeDesignator = 'LN'
    item.CodeMeaning = 'Ventricular rate'
    item.MeasuredValueSequence = [Dataset()]
    item.MeasuredValueSequence[0].NumericValue = measurements.get('ventricular_rate', '')
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence = [Dataset()]
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeValue = 'uV'
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeMeaning = 'microvolt'
    ds[0x0040, 0x0275].value.append(item)

    # Add other measurements similarly if needed...

def add_waveform_data(ds, data, metadata):
    lead_order = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
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
    waveform_item.SamplingFrequency = metadata.get('sample_frequency', '')
    waveform_item.WaveformBitsAllocated = 16
    waveform_item.WaveformSampleInterpretation = 'SS'
    waveform_data = np.zeros((num_samples, num_leads))
    waveform_item.ChannelDefinitionSequence = Sequence()

    for i, lead_id in enumerate(lead_order):
        channel_def_item = Dataset()
        channel_def_item.ChannelNumber = i + 1
        channel_def_item.ChannelLabel = lead_id
        channel_def_item.WaveformBitsStored = 16
        channel_def_item.ChannelSourceSequence = Sequence([Dataset()])
        source = channel_def_item.ChannelSourceSequence[0]
        source.CodeValue = lead_id
        source.CodingSchemeDesignator = 'MDC'
        source.CodeMeaning = lead_id
        channel_def_item.MeasurementUnitsCodeSequence = Sequence([Dataset()])
        channel_def_item.MeasurementUnitsCodeSequence[0].CodeValue = 'uV'
        channel_def_item.MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = 'UCUM'
        channel_def_item.MeasurementUnitsCodeSequence[0].CodeMeaning = 'microvolt'
        waveform_item.ChannelDefinitionSequence.append(channel_def_item)
        waveform_data[:, i] = data[lead_id] * 1000

    waveform_item.WaveformData = waveform_data.astype(np.int16).tobytes()
    ds.WaveformSequence.append(waveform_item)

def add_annotations(ds, metadata):
    ds.WaveformAnnotationSequence = Sequence()
    annotation_group_number = 1  # start from 1 for DICOM compliance

    for diagnosis in metadata.get('diagnosis', []):
        annotation_item = Dataset()
        annotation_item.ReferencedWaveformChannels = [1]
        annotation_item.AnnotationGroupNumber = annotation_group_number
        annotation_item.UnformattedTextValue = diagnosis
        ds.WaveformAnnotationSequence.append(annotation_item)
        annotation_group_number += 1

    # Add QRSTimes annotations
    # for qrs in metadata.get('qrstimes', []):
    #     annotation_item = Dataset()
    #     annotation_item.ReferencedWaveformChannels = [1]
    #     annotation_item.AnnotationGroupNumber = annotation_group_number
    #     annotation_item.RRIntervalTimeMeasured = pydicom.valuerep.DSfloat(metadata['global_rr'])
    #     annotation_item.AnnotationTime = pydicom.valuerep.DSfloat(qrs['time'])
    #     annotation_item.ConceptNameCodeSequence = Sequence([Dataset()])
    #     annotation_item.ConceptNameCodeSequence[0].CodeValue = 'QRS'
    #     annotation_item.ConceptNameCodeSequence[0].CodingSchemeDesignator = 'DCM'
    #     annotation_item.ConceptNameCodeSequence[0].CodeMeaning = 'QRS complex'
    #     ds.WaveformAnnotationSequence.append(annotation_item)
    #     annotation_group_number += 1

    for rr in metadata.get('rrintervals', []):
        annotation_item = Dataset()
        annotation_item.ReferencedWaveformChannels = [2]
        annotation_item.AnnotationGroupNumber = annotation_group_number
        annotation_item.NumericValue = pydicom.valuerep.DSfloat(rr['interval'])

        # Measurement Units Code Sequence
        annotation_item.MeasurementUnitsCodeSequence = Sequence([Dataset()])
        mu_item = Dataset()
        mu_item.CodeValue = 'ms'
        mu_item.CodingSchemeDesignator = 'UCUM'
        mu_item.CodingSchemeVersion = '1.4'
        mu_item.CodeMeaning = 'millisecond'
        annotation_item.MeasurementUnitsCodeSequence.append(mu_item)
        annotation_group_number += 1

def create_dicom_ecg(data, metadata, output_file, character_set='ISO_IR 192', procedure_code='P2-3120A', procedure_meaning='12 lead ECG'):
    file_meta = create_file_meta()
    ds = FileDataset(output_file, {}, file_meta=file_meta, preamble=b"\0" * 128)
    add_patient_study_info(ds, metadata, character_set, procedure_code, procedure_meaning)
    add_waveform_data(ds, data, metadata)
    add_annotations(ds, metadata)
    ds.save_as(output_file)
    print(f'DICOM file saved as {output_file}')

