"""ETIM denormalization helpers."""

import csv

from src.lib.readers.csv import CSVReader

class Denormalizer:
    """Denormalizes ETIM data structures"""

    def __init__(self):
        self._csv_reader = CSVReader()

    def _read_csv(self, file_path):
        """Read CSV file using shared CSVReader."""
        return self._csv_reader.read(file_path)

    def denormalize_field(self, source_file: str, foreign_key: str, related_file: str, key: str, target_field: str, target_file: str = None):
        """
        Denormalize a specific field in a CSV file using a provided mapping.
        
        """

        group_map = self.get_groups_mapping(related_file, key=key, target_field=target_field)
        
        art_class_csv = self._read_csv(source_file)
        art_class_headers = art_class_csv['headers']
        art_class_rows = art_class_csv['rows']

        artgroupid_idx = art_class_headers.index(foreign_key)
        # insert new column
        art_class_headers.insert(artgroupid_idx + 1, target_field)

        for row in art_class_rows:
            group_id = row[artgroupid_idx]
            group_desc = group_map.get(group_id, '')
            row.insert(artgroupid_idx + 1, group_desc)

        # save the new table to ETIM-denormalized/ETIMARTCLASS-denormalized.csv
        if target_file:
        # remove file if exists
            if target_file.exists():
                target_file.unlink()
            with target_file.open('w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(art_class_headers)
                writer.writerows(art_class_rows)

        return art_class_rows

    def get_groups_mapping(self, file, key: str, target_field: str):

        art_group_csv = self._csv_reader.read(file)
        art_group_headers = art_group_csv['headers']
        art_group_rows = art_group_csv['rows']

        if key not in art_group_headers:
            raise ValueError(f"{file} must contain {key} column")
        
        if target_field not in art_group_headers:
            raise ValueError(f"{file} must contain {target_field} column")
        
        group_desc_col = target_field 
        group_id_idx = art_group_headers.index(key)
        group_desc_idx = art_group_headers.index(group_desc_col)
        group_desc_map = {}
        
        # build a lookup map with ARTGROUPID as key and group description as value
        for row in art_group_rows:
            group_id = row[group_id_idx]
            group_desc = row[group_desc_idx]
            group_desc_map[group_id] = group_desc 
            
        
        return group_desc_map

