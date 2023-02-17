This is version 1.0RC3 of VAERity, a program designed to work with the US Vaccine
Adverse Events Reporting System or VAERS, specifically the downloadable files
available at https://vaers.hhs.gov/data/datasets.html

Its eventual goal is to act as a proxy for development of a rounded data exploration
and machine learning tool, a common platform to make it easy to deploy, with a minimum
of additional code, a means of querying large data sets graphically using a variety of
standard tools.  Such a function would free data scientists from the need to focus on
repetitious code and provides a user interface able to be used by developers/data
scientists and non technical personnel alike.  The road to other data sets is roughly
3 months of development and UA testing. with 1 release per month.  That's an awful lot
of coffees :-).  Thankfully, there's https://www.buymeacoffee.com/vaerity and Roma love
chicken.  Roma work for chicken!  This software written for Beltalowda ;) with shout out
to Josephus Miller for inspiration.  He knows all the right angles.

VAERity is released under the Creative Commons 3.0 License - Attribution, Non-Commercial,
Share-Alike.  Development for VAERity began at the end of November 2022 during an upskilling
between roles to re-enter the world of data science.  I believe it was Hal Turner's website
running an article that linked to VAERS, and I very quickly saw the file formats and almost
immediately determined that this was a very special data set, from the earliest days of
playing with it in a Jupyter Notebook.

Written in Python, VAERity uses vaex and pandas for the data manipulation, performing
automatic conversion to hdf5 when no hdf5 versions of the CSV files exist.  All years
are opened as a single dataset at present.  If NonDomestic is present, it is loaded also.

The early development was bare matplotlib with a GUI based agg.  Before long I realised
that to get more complex in our investigations I needed to flip this on its head, a GUI
with a bare agg, using kivy garden, and thus VAERity 0.1 was born.

As development progressed, the abstraction grew until I began to envision a system of
declarative XML based data sets paired with Graphs unique/specific to those data sets,
with compilable python bindings / classes to do what cannot be written declaratively
in XML.  This would be the end goal after the existing functionality was brought to a
state to be usable by those investigating the very interesting data in VAERS.  Yup.
Pluggable datasets.  Pluggable, multiplexing data sets at that, so that eventually
queries spanning these data sets can be made easy and done in a GUI.

For now, though, one data set would have to do ;-)

It is my sincere hope that with this release candidate finds its usefulness and support
within the community.  Current future development ideas we would welcome feedback on are
further integration around MedDRA, integration of UK health report data sets, and we
welcome feedback on any other health related data sets foreign or otherwise that could
be integrated, including mortality figures.  A good outcome would be to crowd fund
transparency on available health related data sets to ordinary citizens, to make having
objective discussions easier.  This of course has value in business and politics as well
as to ordinary people.  Risk management is important everywhere, not just in business.
Having the right data to mitigate the risk in the decision making process is invaluable.

The program, although still experimental, can be considered stable, and a basic user manual
is included.  I hope you'll enjoy exploring the VAERS data set as much as I have!

Some quick FAQ points:
1. VAERity is not political.  Our aim is increased data transparency to drive better risk
management decisions, a very Agile concept.

As Agile moves out of the solely software and solution delivery sphere into the wider realm
of business, a key takeaway from the existing methodology is that transparent and quantifiable
data is key to good risk management.  In the current fluid business environment, those who would
survive must have access to the right data insights.

2. All included meme images were sourced from publicly available images on the internet, and were
checked for copyright or licensing information before inclusion.  However if anything has been
missed, let me know and it can be dealt with swiftly.

3. The comic images on start up are a way of creating humor from what is in reality a very dark
and often serious subject.  They are not meant to push a particular view and if one offends you,
simply delete it and add your own.

4. If further development goes ahead, my ideal would be to communicate regular updates via patreon,
while non patreon users can still derive the benefits from the regular push updates throughout
development by following this Github.

5. I also hope to deliver to any programmer patrons videos on the development of the program
and the knowledge gleaned about vaex, kivy and threading that has not yet been covered fully
on youtube.  Instructional videos are also in the works.

Reach out via one of our channels if you have any questions.  Happy hunting!

leprechaunt33, 14th-15th February 2022.
