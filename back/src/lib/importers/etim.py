"""ETIM denormalization workflow."""

from pathlib import Path

from src.lib.denormalizers.denormalizer import Denormalizer as BaseDenormalizer
from src.lib.readers.csv import CSVReader

class Denormalizer:
    """Denormalizes ETIM data structures"""

    def __init__(self, storage_dir: Path = None):
        """
        Initialize denormalizer with storage directory.
        
        Args:
            storage_dir: Path to storage directory containing ETIM CSV files
        """
        if storage_dir is None:
            back_root = Path(__file__).resolve().parents[3]
            storage_dir = back_root / 'var' / 'storage' / 'ETIM-9.0-ALL-SECTORS-CSV-METRIC-EI-2022-12-05'
        self.storage_dir = Path(storage_dir)
        self.target_dir = self.storage_dir.parent / 'ETIM-denormalized'
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self._csv_reader = CSVReader()

        self.denormalizer = BaseDenormalizer()

    def _read_csv(self, filename: str):
        """
        Read CSV file using shared CSVReader.
        """
        file_path = self.storage_dir / filename
        return self._csv_reader.read(file_path)

    def denormalize(self):
        """
        Denormalize etim csv files and return results.
        
        Returns:
            list: Array of denormalized data
        """

        # 1.ETIMARTCLASS.csv
        # 1.1.we open the csv file ETIMARTCLASS.csv from ETIM-9.0-ALL-SECTORS-CSV-METRIC-EI-2022-12-05
        
        relations = [[
            'ETIMARTCLASS.csv',
            'ARTGROUPID',
            'ETIMARTGROUP.csv',
            'ARTGROUPID',
            'GROUPDESC'
        ]]

        rows = []

        for relation in relations:
            rows = self.denormalizer.denormalize_field(
                source_file= self.storage_dir / relation[0],
                foreign_key=relation[1],
                related_file=self.storage_dir / relation[2],
                key=relation[3],
                target_field=relation[4],
                target_file=self.target_dir / f"{Path(relation[0]).stem}.csv"
            )


        return rows

