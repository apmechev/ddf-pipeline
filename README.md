# ddf-pipeline

## prerequisites

DDFacet and KillMS, of course: astropy; pyrap

emcee for bootstrap, and
mpi4py if you want to use MPI to speed up emcee (not typically necessary).

reproject for the mosaicing script.

The bootstrap code also expects the script directory (this directory)
to be on the user's PATH.

## running pipeline

pipeline.py takes one option, the name of a config file. This is in the standard python ConfigParser format. If no config file is given, the code prints out a skeleton of a file with some default values.

A minimal set of parameters is

```
[data]
mslist=mslist.txt
```
where `mslist.txt` contains a list of MSs to be used for the initial round of phase and then amplitude self-calibration. However, in the current state of the code you will almost certainly want to specify other parameters, such as `psf_arcsec` in the `[image]` block.

## bootstrap

Flux scale bootstrap requires the following in the config file:

```
[control]
bootstrap=True

[bootstrap]
catalogues=['cat1.fits','cat2.fits'...]
radii=[40,10..]
frequencies=[74e6,327e6,...]
```

Catalogues, radii, frequencies are lists in Python list
format.

* catalogue must be a list of existing files in PyBDSM format
(i.e. they must contain RA, Dec, Total_flux, E_Total_flux). Some suitable
files are available at http://www.extragalactic.info/bootstrap/ . 

* radii are the separation distances in arcsec to use for each catalogue. If not specified this will default to 10 arcsec for each, but this is probably not what you want.

* frequencies are the frequencies of each catalogue in Hz.

Optionally you may supply in the `bootstrap` block a list of names which will be used in the
crossmatch tables to identify the catalogues (`names`) and a
list of group identifiers for each catalogue (`groups`). If `groups` is used, matches from one or more of the catalogues in each group are required for a source to be fitted. The default is that a match in each individual catalogue is required.

Bootstrap operates on the `mslist` specified and so needs that to contain enough measurement sets to do the fitting. 5 or 6 is a good compromise.

If bootstrap runs successfully then a `SCALED_DATA` column will be generated and used thereafter for imaging. If you want to remove this, e.g. to rerun bootstrap, then the `remove_bootstrap.py` script can be used to delete the column from a list of measurement sets. To rerun bootstrap from scratch you will also need to delete other files you may not want, e.g. `crossmatch-*`.

Results can be plotted using the `plot_factors.py` script.

## masking

If use of the TGSS catalogue to generate masks for bright sources is required, the full path to the catalogue must be specified in the masking block:

```
[masking]
tgss=/stri-data/mjh/tgss/TGSSADR1_7sigma_catalog.fits
```

Enable the use of masks for extended sources with `tgss_extended=True`.

## cleanup

If you want to discard all the self-calibration for a run and start again, delete all output images you don't want and run `archive_old_solutions.py` (takes the parameter file name as an argument).

## data preparation for Tier 1

Run a Tier 1 reduction as follows:

* `download.py L229587` to make a directory `L229587` and download all the reduced data from SARA into it.
* Make this your working directory
* `unpack.py` to unpack the tar files and make a sensible directory structure
* `make_mslists.py` to make the mslist files &mdash; this ensures that fully flagged data are excluded
* Copy a suitable config file, e.g. `tier1.cfg`, amending the paths suitably.
* Run the pipeline.

At Herts the script `run_pipeline.py` will accomplish all of this, but
needs modifying on a per-user, per-system basis to use the right
directories and start the pipeline run batch job.

## quality pipeline

Once the pipeline has run you can use `quality_pipeline.py` to get
some basic quality information, including positional and flux scale
offsets. Copy `quality_pipeline.cfg` and amend suitably. By default
this looks for the standard pipeline products in the current working
directory. Catalogues used in the quality pipeline must conform (at
least roughly) to the PyBDSM format. See
http://www.extragalactic.info/bootstrap/ for examples.

TGSS and FIRST catalogues must be provided here to allow the code to run.

## mosaicing

Make a mosaic of adjacent observations from the pipeline with the
`mosaic.py` script. At a minimum it needs directories specified with
the `--directories` argument which contain standard pipeline
output. You can also determine the noise from the image with the
`--find_noise` option and remove global offsets with respect to FIRST
(quality pipeline must have been run first) with the `--shift` option.
