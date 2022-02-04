import csv
import logging


class SummariesSinkCsv:
    def __init__(self, file_name, output_fields):
        self.file_name = file_name
        self.output_fields = output_fields
        self.logger = logging.getLogger(__name__)

    def open_sink(self):
        # this should probably not be in an initializer
        self.csvfile = open(self.file_name + ".csv", "w")
        self.writer = csv.DictWriter(
            self.csvfile, fieldnames=self.output_fields, restval="0"
        )
        self.writer.writeheader()
        return self

    def write_row(self, message_summary):
        self.writer.writerow(message_summary)

    def close_sink(self):
        self.csvfile.close()
