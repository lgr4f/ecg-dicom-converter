import xml.etree.ElementTree as ET
import base64
import struct
import numpy as np
import warnings
import logging

logging.basicConfig(level=logging.INFO)
def decode_waveform_data(waveform_data, amplitude_units_per_bit):
    decoded_data = base64.b64decode(waveform_data.strip())
    data_points = struct.unpack('<' + 'h' * (len(decoded_data) // 2), decoded_data)
    data_points_uV = np.array(data_points) * amplitude_units_per_bit * 0.001
    return data_points_uV


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
        rhythm_leads = {}
        rhythm_lead_filters = {}
        rhythm_lead_sample_count = {}
        found_rhythm_waveform = False

        median_leads = {}
        median_lead_filters = {}
        median_lead_sample_count = {}
        found_median_waveform = False

        for waveform in root.findall('.//Waveform'):
            waveform_type = waveform.find('WaveformType')
            if waveform_type is not None and waveform_type.text == "Rhythm":
                found_rhythm_waveform = True
                for lead in waveform.findall('LeadData'):
                    lead_id = lead.find('LeadID').text
                    amplitude_units = convert_to_float(lead.find('LeadAmplitudeUnitsPerBit').text)
                    waveform_data = lead.find('WaveFormData').text
                    data_points = decode_waveform_data(waveform_data, amplitude_units)
                    rhythm_leads[lead_id] = data_points

                    rhythm_lead_filters[lead_id] = {
                        'HighPassFilter': waveform.findtext('HighPassFilter', '0'),
                        'LowPassFilter': waveform.findtext('LowPassFilter', '0'),
                        'ACFilter': waveform.findtext('ACFilter', '0')
                    }

                    rhythm_lead_sample_count[lead_id] = int(lead.findtext('LeadSampleCountTotal', 0))

            elif waveform_type is not None and waveform_type.text == "Median":
                found_median_waveform = True
                for lead in waveform.findall('LeadData'):
                    lead_id = lead.find('LeadID').text
                    amplitude_units = convert_to_float(lead.find('LeadAmplitudeUnitsPerBit').text)
                    waveform_data = lead.find('WaveFormData').text
                    data_points = decode_waveform_data(waveform_data, amplitude_units)
                    median_leads[lead_id] = data_points

                    median_lead_filters[lead_id] = {
                        'HighPassFilter': waveform.findtext('HighPassFilter', '0'),
                        'LowPassFilter': waveform.findtext('LowPassFilter', '0'),
                        'ACFilter': waveform.findtext('ACFilter', '0')
                    }

                    median_lead_sample_count[lead_id] = int(lead.findtext('LeadSampleCountTotal', 0))

        # Derived leads (only if I and II are present)
        if found_rhythm_waveform:
            if 'I' in rhythm_leads and 'II' in rhythm_leads:
                rhythm_leads['III'] = np.subtract(rhythm_leads['II'], rhythm_leads['I'])
                rhythm_leads['aVR'] = -(rhythm_leads['I'] + rhythm_leads['II']) / 2
                rhythm_leads['aVL'] = rhythm_leads['I'] - (rhythm_leads['II'] / 2)
                rhythm_leads['aVF'] = rhythm_leads['II'] - (rhythm_leads['I'] / 2)

                rhythm_lead_filters['III'] = rhythm_lead_filters.get('II', {})
                rhythm_lead_filters['aVR'] = rhythm_lead_filters.get('I', {})
                rhythm_lead_filters['aVL'] = rhythm_lead_filters.get('I', {})
                rhythm_lead_filters['aVF'] = rhythm_lead_filters.get('II', {})
            else:
                logging.warning("Leads I and II are required to derive III, aVR, aVL, aVF for Rhythm waveform.")
        else:
            logging.warning("No 'Rhythm' waveform found in the XML.")

        if found_median_waveform:
            if 'I' in median_leads and 'II' in median_leads:
                median_leads['III'] = np.subtract(median_leads['II'], median_leads['I'])
                median_leads['aVR'] = -(median_leads['I'] + median_leads['II']) / 2
                median_leads['aVL'] = median_leads['I'] - (median_leads['II'] / 2)
                median_leads['aVF'] = median_leads['II'] - (median_leads['I'] / 2)

                median_lead_filters['III'] = median_lead_filters.get('II', {})
                median_lead_filters['aVR'] = median_lead_filters.get('I', {})
                median_lead_filters['aVL'] = median_lead_filters.get('I', {})
                median_lead_filters['aVF'] = median_lead_filters.get('II', {})
            else:
                logging.warning("Leads I and II are required to derive III, aVR, aVL, aVF for Median waveform.")
        else:
            logging.warning("No 'Median' waveform found in the XML.")

        # Metadata extraction
        metadata = {
            'PatientID': '',
            'RhythmLeadFilters': rhythm_lead_filters,
            'RhythmCount': rhythm_lead_sample_count,
            'MedianLeadFilters': median_lead_filters,
            'MedianCount': median_lead_sample_count
        }

        patient = root.find('.//PatientDemographics')
        if patient is not None:
            metadata['PatientID'] = patient.findtext('PatientID', '')
            last_name = patient.findtext('PatientLastName')
            first_name = patient.findtext('PatientFirstName')
            if last_name and first_name:
                metadata['PatientName'] = f"{last_name}^{first_name}".strip('^')
            metadata['PatientAge'] = patient.findtext('PatientAge')
            metadata['Gender'] = patient.findtext('Gender')
            metadata['DateofBirth'] = patient.findtext('DateofBirth')
        else:
            warnings.warn("No PatientDemographics section found in XML.")

        test = root.find('.//TestDemographics')
        if test is not None:
            metadata.update({
                'AcquisitionDate': test.findtext('AcquisitionDate'),
                'AcquisitionTime': test.findtext('AcquisitionTime'),
                'AcquisitionDevice': test.findtext('AcquisitionDevice'),
                'SiteName': test.findtext('SiteName'),
                'LocationName': test.findtext('LocationName')
            })

        order = root.find('.//Order')
        if order is not None:
            metadata.update({
                'AdmitTime': order.findtext('AdmitTime'),
                'AdmitDate': order.findtext('AdmitDate'),
                'EditTime': order.findtext('EditTime'),
                'EditDate': order.findtext('EditDate')
            })

        measurements = root.find('.//RestingECGMeasurements')
        if measurements is not None:
            metadata['measurements'] = {
                'VentricularRate': measurements.findtext('VentricularRate'),
                'AtrialRate': measurements.findtext('AtrialRate'),
                'PRInterval': measurements.findtext('PRInterval'),
                'QRSDuration': measurements.findtext('QRSDuration'),
                'QTInterval': measurements.findtext('QTInterval'),
                'QTCorrected': measurements.findtext('QTCorrected'),
                'PAxis': measurements.findtext('PAxis'),
                'RAxis': measurements.findtext('RAxis'),
                'TAxis': measurements.findtext('TAxis'),
                'QRSCount': measurements.findtext('QRSCount'),
                'QOnset': measurements.findtext('QOnset'),
                'QOffset': measurements.findtext('QOffset'),
                'POnset': measurements.findtext('POnset'),
                'POffset': measurements.findtext('POffset'),
                'TOffset': measurements.findtext('TOffset')
            }
            base = measurements.findtext('ECGSampleBase')
            exp = measurements.findtext('ECGSampleExponent')
            if base and exp:
                metadata['SampleFrequency'] = float(base) * (10 ** float(exp))

        # Diagnoses
        diagnosis = root.find('.//Diagnosis')
        metadata['diagnosis'] = [d.findtext('StmtText').strip()
                                 for d in diagnosis.findall('.//DiagnosisStatement')
                                 if d.findtext('StmtText')]

        # QRS Times
        metadata['QRSTimes'] = []
        for qrs in root.findall('.//QRSTimesTypes/QRS'):
            try:
                metadata['QRSTimes'].append({
                    'number': int(qrs.findtext('Number', 0)),
                    'type': int(qrs.findtext('Type', 0)),
                    'time': int(qrs.findtext('Time', 0))
                })
            except Exception as e:
                logging.warning(f"Failed to parse QRS time: {e}")

        rr = root.findtext('.//QRSTimesTypes/GlobalRR')
        metadata['RRInterval'] = int(rr) if rr else None

        qtrggr = root.findtext('.//QRSTimesTypes/QTRGGR')
        metadata['qtrggr'] = int(qtrggr) if qtrggr else None

        # Final return: two-lead list and metadata
        return rhythm_leads, median_leads, metadata

    except Exception as e:
        raise ValueError(f"Error extracting Muse XML data from {file_path}: {str(e)}")


def extract_data(file_path):
    try:
        if file_path.endswith('.xml'):
            return extract_muse_xml_data(file_path)
        else:
            raise ValueError(f"Unsupported file format in {file_path}. Please provide a Muse XML (.xml) file.")
    except Exception as e:
        raise ValueError(f"Error extracting data from {file_path}: {str(e)}")
