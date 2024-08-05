import wfdb
import xml.etree.ElementTree as ET
import base64
import struct
import numpy as np

def extract_wfdb_data(file_path):
    record = wfdb.rdrecord(file_path[:-4])
    data = record.p_signal
    metadata = {
        'patient_name': record.comments[0].split(': ')[1] if 'Patient' in record.comments[0] else 'Unknown^Patient',
        'patient_id': record.comments[1].split(': ')[1] if 'ID' in record.comments[1] else 'Unknown',
        'patient_age': None,
        'patient_sex': None
    }
    return data, metadata

def decode_waveform_data(waveform_data, amplitude_units_per_bit):
    decoded_data = base64.b64decode(waveform_data.strip())
    data_points = struct.unpack('<' + 'h' * (len(decoded_data) // 2), decoded_data)
    data_points_mV = np.array(data_points) * amplitude_units_per_bit * 0.001
    return data_points_mV

def convert_to_float(value):
    try:
        value = str(value).replace(',', '.')
        value = float(value.replace('+', '-'))
        return value
    except ValueError:
        return float('nan')

def extract_muse_xml_data(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    leads = {}

    for waveform in root.findall('.//Waveform'):
        for lead in waveform.findall('LeadData'):
            lead_id = lead.find('LeadID').text
            amplitude_units_per_bit = convert_to_float(lead.find('LeadAmplitudeUnitsPerBit').text)
            waveform_data = lead.find('WaveFormData').text
            data_points_mV = decode_waveform_data(waveform_data, amplitude_units_per_bit)
            leads[lead_id] = data_points_mV

    leads['III'] = np.subtract(leads['II'], leads['I'])
    leads['aVR'] = -(leads['I'] + leads['II']) / 2
    leads['aVL'] = leads['I'] - (leads['II'] / 2)
    leads['aVF'] = leads['II'] - (leads['I'] / 2)

    # Extract additional metadata
    patient = root.find('.//PatientDemographics')
    test = root.find('.//TestDemographics')
    order = root.find('.//Order')
    measurements = root.find('.//RestingECGMeasurements')

    metadata = {
        'patient_name': (patient.findtext('PatientLastName') + '^' + patient.findtext('PatientFirstName')).strip('^'),
        'patient_id': patient.findtext('PatientID'),
        'patient_age': patient.findtext('PatientAge'),
        'patient_sex': patient.findtext('Gender'),
        'patient_birthdate': patient.findtext('DateofBirth'),
        'diagnosis': [],
        'acquisition_date': test.findtext('AcquisitionDate'),
        'acquisition_time': test.findtext('AcquisitionTime'),
        'device': test.findtext('AcquisitionDevice'),
        'site': test.findtext('SiteName'),
        'admit_date': order.findtext('AdmitDate'),
        'admit_time': order.findtext('AdmitTime'),
        'measurements': {  # Extracting only a few for example
            'ventricular_rate': measurements.findtext('VentricularRate'),
            'atrial_rate': measurements.findtext('AtrialRate'),
            'pr_interval': measurements.findtext('PRInterval'),
            'qrs_duration': measurements.findtext('QRSDuration'),
            'qt_interval': measurements.findtext('QTInterval'),
            'qt_corrected': measurements.findtext('QTCorrected'),
        },
        'sample_frequency': float(measurements.findtext('ECGSampleBase'))*(10 ** float(measurements.findtext('ECGSampleExponent'))),
    }

    for diagnosis in root.findall('.//DiagnosisStatement'):
        text = diagnosis.findtext('StmtText')
        if text:
            metadata['diagnosis'].append(text.strip())

    return leads, metadata

def extract_data(file_path):
    if file_path.endswith('.hea'):
        return extract_wfdb_data(file_path)
    elif file_path.endswith('.xml'):
        return extract_muse_xml_data(file_path)
    else:
        raise ValueError('Unsupported file format. Please provide a WFDB (.hea) or Muse XML (.xml) file.')

