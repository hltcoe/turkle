History
-------

0.4.0
+++++
* The CSV input file is expected to be encoded in UTF-8, and the format is
  the excel style, with
  * `,` as the delimiter, 
  * double quote `"` characters surrounding an entry if it contains commas.
  * rows delimited by `\r` or `\r\n`.
* The `dump_results` command's arguments changed.
  * The absolute path to where the template file was located when the HITs were
    published is now required. This argument acts as a filter so that only
    completed HITs from the same template are dumped.
* The `dump_results` command writes a CSV formatted file (matching the format
  of the CSV input file), instead of a file containing tab-delimited text.
* The HIT detail page shows template path and input csv file from which the HIT
  was generated.

0.3
+++

0.2
+++

0.1
+++
