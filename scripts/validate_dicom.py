import scripts.dicom_validator.validate_iods as vi  # Importiere das andere Skript als Modul
import os
import csv


def count_error_categories(errors):
    # Initialisiere die Zähler für die verschiedenen Kategorien
    error_counts = {
        'missing': 0,
        'unexpected': 0,
        'conflicting': 0,
        'other': 0
    }

    for file_path, error_details in errors.items():
        for section, tags in error_details.items():
            for error_message in tags:
                if 'missing' in error_message.lower():
                    error_counts['missing'] += 1
                elif 'unexpected' in error_message.lower():
                    error_counts['unexpected'] += 1
                elif 'conflicting' in error_message.lower():
                    error_counts['conflicting'] += 1
                else:
                    error_counts['other'] += 1

    return error_counts


def save_error_counts_to_csv(csv_file_path, file_number, error_counts):
    # Prüfe, ob die CSV-Datei schon existiert
    file_exists = os.path.isfile(csv_file_path)

    # Öffne die CSV-Datei im Anhängemodus
    with open(csv_file_path, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';')

        # Wenn die Datei neu ist, schreibe die Spaltenüberschrift
        if not file_exists:
            csv_writer.writerow(['File Number', 'Missing', 'Unexpected', 'Conflicting', 'Other'])

        # Schreibe die Zeile mit den Fehlerkategorien
        csv_writer.writerow([
            file_number,
            error_counts['missing'],
            error_counts['unexpected'],
            error_counts['conflicting'],
            error_counts['other']
        ])


def validate_dicom_file(dicom_file, pseudonymization_file_number):
    # Definiere den Pfad zur CSV-Datei
    csv_file_path = os.path.join(os.path.dirname(dicom_file), '../validator.csv')

    # Bereite die Argumente für das dicom_validator-Modul vor
    args = [
        str(dicom_file),  # Pfad zur DICOM-Datei
        "--verbose",  # Optional: Ausführliche Ausgabe aktivieren
        "--force-read",  # Optional: DICOM-Dateien ohne Header erzwingen
        "--suppress-vr-warnings",  # Optional: VR-Warnungen unterdrücken
    ]

    # Rufe die main-Funktion des dicom_validator-Moduls mit den vorbereiteten Argumenten auf
    errors = vi.main(args)

    # Zähle die Fehlerkategorien (missing, unexpected, conflicting, etc.)
    error_counts = count_error_categories(errors)

    # Speichere die Fehlerkategorien in die CSV-Datei
    save_error_counts_to_csv(csv_file_path, pseudonymization_file_number, error_counts)

    # Gebe die gezählten Fehlerkategorien zurück oder verwende sie zur weiteren Verarbeitung
    return error_counts
