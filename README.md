
# DICOM-ECG-Converter

This package provides tools to extract ECG data from Muse XML format and convert it to DICOM format.

## Installation

You can install the package using pip:

```sh
pip install .
```

## Usage

Here is an example of how to use this package:

```sh
ecg_dicom_converter path_to_input_file path_to_output
OR
ecg_dicom_converter path_to_input path_to_output -r
```

## Usage of DICOM ECGs
How to extract the raw signal of a DICOM ECG via Python
```sh
import pydicom
import numpy as np

dicom_data = pydicom.dcmread(path_to_dicom_ecg)
waveform_seq = dicom_data.WaveformSequence[0]
compressed_signal = waveform_seq.WaveformData
raw_signal = np.frombuffer(compressed_signal, dtype=np.int16)
num_samples = waveform_seq.NumberOfWaveformSamples
num_channels = waveform_seq.NumberOfWaveformChannels
waveform_data = raw_signal.reshape((num_samples, num_channels))
```
