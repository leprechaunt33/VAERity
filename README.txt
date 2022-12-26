This is version 1 of VAERity, a program designed to work with the US Vaccine
Adverse Events Reporting system or VAERS, specifically the downloadable files
available at https://vaers.hhs.gov/data/datasets.html

VAERity is written in Python.  It uses vaex and pandas for the data 
manipulation, performing automatic conversion to hdf5 when no hdf5 
versions of the CSV files exist.  All years are opened as a single 
dataset at present.

It uses kivy to wrap a GUI with threading for individual reports to 
keep the  GUI as responsive as possible.  At present this can be 
considered highly alpha and experimental until it is pushed to a 
wider audience.

The author publishes this program under a Creative Commons License, 
and claims no warranty of fitness for any purpose whatsoever.  Use 
it at your own risk.  It may kill your cat if you put it in a box, 
or maybe that's not the program or Schroedinger's fault ;-).

Have fun and enjoy exploring the data-set with this program!  Remember, 
data science is meant to be FUN!

