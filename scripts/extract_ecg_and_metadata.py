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
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        leads = {}
        lead_filters = {}

        for waveform in root.findall('.//Waveform'):
            for lead in waveform.findall('LeadData'):
                lead_id = lead.find('LeadID').text
                amplitude_units_per_bit = convert_to_float(lead.find('LeadAmplitudeUnitsPerBit').text)
                waveform_data = lead.find('WaveFormData').text
                data_points_mV = decode_waveform_data(waveform_data, amplitude_units_per_bit)
                leads[lead_id] = data_points_mV

                # Extract channel-specific filter values
                lead_filters[lead_id] = {
                    'HighPassFilter': waveform.findtext('HighPassFilter', '0'),
                    'LowPassFilter': waveform.findtext('LowPassFilter', '0'),
                    'ACFilter': waveform.findtext('ACFilter', '0')
                }

        # Calculate the manually derived leads
        leads['III'] = np.subtract(leads['II'], leads['I'])
        leads['aVR'] = -(leads['I'] + leads['II']) / 2
        leads['aVL'] = leads['I'] - (leads['II'] / 2)
        leads['aVF'] = leads['II'] - (leads['I'] / 2)


        # Inherit the filter settings from the original leads
        lead_filters['III'] = lead_filters['II']  # III is derived from II and I, choose II or I
        lead_filters['aVR'] = lead_filters['I']   # aVR is derived from I and II, choose I or average
        lead_filters['aVL'] = lead_filters['I']   # aVL is derived from I and II, choose I
        lead_filters['aVF'] = lead_filters['II']  # aVF is derived from II and I, choose II



        # Extract additional metadata
        patient = root.find('.//PatientDemographics')
        test = root.find('.//TestDemographics')
        order = root.find('.//Order')
        measurements = root.find('.//RestingECGMeasurements')

        metadata = {
            'patient_id': patient.findtext('PatientID'),
            'lead_filters': lead_filters
        }

        if patient is not None:
            metadata['patient_name'] = (
                        patient.findtext('PatientLastName') + '^' + patient.findtext('PatientFirstName')).strip(
                '^') if patient.findtext('PatientLastName') and patient.findtext('PatientFirstName') else None
            metadata['patient_age'] = patient.findtext('PatientAge')
            metadata['patient_sex'] = patient.findtext('Gender')
            metadata['patient_birthdate'] = patient.findtext('DateofBirth')

        if test is not None:
            metadata['acquisition_date'] = test.findtext('AcquisitionDate')
            metadata['acquisition_time'] = test.findtext('AcquisitionTime')
            metadata['device'] = test.findtext('AcquisitionDevice')
            metadata['site'] = test.findtext('SiteName')

        # needs a connetion to the HIS for the information
        if order is not None:
            metadata['admit_time'] = order.findtext('AdmitTime')
            metadata['admit_date'] = order.findtext('AdmitDate')

        if measurements is not None:
            metadata['measurements'] = {
                'ventricular_rate': measurements.findtext('VentricularRate'),
                'atrial_rate': measurements.findtext('AtrialRate'),
                'pr_interval': measurements.findtext('PRInterval'),
                'qrs_duration': measurements.findtext('QRSDuration'),
                'qt_interval': measurements.findtext('QTInterval'),
                'qt_corrected': measurements.findtext('QTCorrected'),
            }
            metadata['sample_frequency'] = float(measurements.findtext('ECGSampleBase')) * (
                        10 ** float(measurements.findtext('ECGSampleExponent'))) if measurements.findtext(
                'ECGSampleBase') and measurements.findtext('ECGSampleExponent') else None

        metadata['diagnosis'] = []
        for diagnosis in root.findall('.//DiagnosisStatement'):
            text = diagnosis.findtext('StmtText')
            if text:
                metadata['diagnosis'].append(text.strip())

        metadata['qrstimes'] = []
        for qrs in root.findall('.//QRSTimesTypes/QRS'):
            metadata['qrstimes'].append({
                'number': int(qrs.findtext('Number')),
                'type': int(qrs.findtext('Type')),
                'time': int(qrs.findtext('Time'))
            })

        metadata['global_rr'] = int(root.findtext('.//QRSTimesTypes/GlobalRR')) if root.findtext(
            './/QRSTimesTypes/GlobalRR') else None
        metadata['qtrggr'] = int(root.findtext('.//QRSTimesTypes/QTRGGR')) if root.findtext(
            './/QRSTimesTypes/QTRGGR') else None

        return leads, metadata
    except Exception as e:
        raise ValueError(f"Error extracting Muse XML data from {file_path}: {str(e)}")


def extract_data(file_path):
    try:
        if file_path.endswith('.hea'):
            return extract_wfdb_data(file_path)
        elif file_path.endswith('.xml'):
            return extract_muse_xml_data(file_path)
        else:
            raise ValueError(f"Unsupported file format in {file_path}. Please provide a WFDB (.hea) or Muse XML (.xml) file.")
    except Exception as e:
        raise ValueError(f"Error extracting data from {file_path}: {str(e)}")
