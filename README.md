# hllib.py
Python binding for HLLib version 2.4.5.

HLLib is a package library for Half-Life that abstracts several package formats
(e.g. GCF, NCF, VPK, WAD, etc.) and provides a simple interface for all of them.
It can be used to read, extract, validate, defragment, etc., package contents.

The hllib.py module is the Python binding. It requires the HLLib C library.
Download the HLLib C library separately from http://nemesis.thewavelength.net/.

hlextract.py is an example command-line application modeled after HLExtract,
the example application that is packaged with the HLLib C library.
