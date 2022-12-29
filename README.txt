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
wider audience and tested on multiple configurations.

In line with this, the author publishes this program under a
Creative Commons License, and claims no warranty of fitness for
any purpose whatsoever.  Use it at your own risk.  It may kill
your cat if you put it in a box, or maybe that's not the program
or Schroedinger's fault ;-).

Have fun and enjoy exploring the data-set with this program!  Remember, 
data science is meant to be FUN!

Despite this being a first release, the program works admirably for
even queries that would be difficult in openvaers, and enables you to
obtain a more complete picture of the data set and its quality (or at
times the lack thereof!)

The program does not convert medical terminology or abbreviations into
simplified form and the person using the program is assumed to be smart
enough to look up the abbreviations on CDC's website (eg the injection
site and vaccine name abbreviations are left as is).

There are plans for future expansion of the program.  Please see the TODO
comments that remain within the committed code.  Beyond these and any
feature requests from the community, I plan on pushing the entire
VAERS symptom set, medical history, allergies and such as appropriate
to an AI text model which I also train on basic medical texts in order
to develop word embeddings to allow for much more intelligent grouping
of reported symptoms and hopefully discover new patterns in it by
comparing word vectors on the various adverse event reports.

More generally with this program my hope is to apply machine learning
techniques to the dataset as well as allowing the end user to continue
that process of allowing the program to learn as the data set grows.

Please note that VAERS is not just for COVID19 reports, it is a much
more rich and varied dataset which includes reports for VARICELLA,
Tetanus, Polio, Flu vaccines and more.  The reports range from patients
who are infants less than a year old up to individuals over 100 years old.
It is able to be used educationally in some respects as a means of teaching
about data quality, as it is a real world dataset with many problems and
limitations which could have been predicted.

Despite bundling humorous animated GIFs off of various meme sites in the
resources folder as a starting point (users can include their own images
on startup), this program is politically and culturally neutral. My own
political, cultural and personal views regarding the pandemic and even
the topic of vaccination are my own and will not be discussed, and the
use of the program in and of itself is not political, but simply a tool
to, as the program's tag line points out, "Uncover truth in data".  I
strongly encourage users to find a forum or social media site that they
feel comfortable using to discuss their findings with the community and
to do so objectively, while being careful where relevant to avoid making
the error of attributing causation where only correlation is shown.  The
insights gained by reviewing the VAERS data set are jumping off points
for deeper investigation, and are not an end in themselves.

Finally, if you enjoy this program or find it useful, I would love to hear
from you!   I am also as of version 1 of this program, between roles, so if
you are impressed by the code and want to hire me, or have a project you
think I might be interested in, I'm open to hearing suggestions. Hit me
up through Github socially, or via email.

leprechaunt33, 29th December 2022.