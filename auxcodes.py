import numpy as np
from scipy.optimize import leastsq
import scipy
import os,sys
from pipeline_logging import run_log
from subprocess import call
from astropy.io import fits
from astropy.wcs import WCS

class bcolors:
   HEADER = '\033[95m'
   OKBLUE = '\033[94m'
   OKGREEN = '\033[92m'
   WARNING = '\033[93m'
   FAIL = '\033[91m'
   ENDC = '\033[0m'

def die(s):
   print bcolors.FAIL+s+bcolors.ENDC
   raise Exception(s)

def report(s):
   print bcolors.OKGREEN+s+bcolors.ENDC

def warn(s):
   print bcolors.OKBLUE+s+bcolors.ENDC

def run(s,proceed=False,dryrun=False,log=None,quiet=False):
   report('Running: '+s)
   if not dryrun:
      if log is None:
         #print 'Log is none, using "call" to run '+s
         retval=call(s,shell=True)
      else:
         retval=run_log(s,log,quiet)
      if not(proceed) and retval!=0:
         os.system('CleanSHM.py')
         die('FAILED to run '+s+': return value is '+str(retval))

      return retval
   else:
      warn('Dry run, skipping this step')

def get_rms(hdu,boxsize=1000,niter=20,eps=1e-6,verbose=False):

    data=hdu[0].data
    if len(data.shape)==4:
       _,_,ys,xs=data.shape
       subim=data[0,0,ys/2-boxsize/2:ys/2+boxsize/2,xs/2-boxsize/2:xs/2+boxsize/2].flatten()
    else:
       ys,xs=data.shape
       subim=data[ys/2-boxsize/2:ys/2+boxsize/2,xs/2-boxsize/2:xs/2+boxsize/2].flatten()
    oldrms=1
    for i in range(niter):
        rms=np.std(subim)
        if verbose: print len(subim),rms
        if np.abs(oldrms-rms)/rms < eps:
            return rms
        subim=subim[np.abs(subim)<5*rms]
        oldrms=rms
    raise Exception('Failed to converge')

def flatten(f):
    """ Flatten a fits file so that it becomes a 2D image. Return new header and data """

    naxis=f[0].header['NAXIS']
    if naxis<2:
        raise RadioError('Can\'t make map from this')
    if naxis==2:
        return f[0].header,f[0].data

    w = WCS(f[0].header)
    wn=WCS(naxis=2)
    
    wn.wcs.crpix[0]=w.wcs.crpix[0]
    wn.wcs.crpix[1]=w.wcs.crpix[1]
    wn.wcs.cdelt=w.wcs.cdelt[0:2]
    wn.wcs.crval=w.wcs.crval[0:2]
    wn.wcs.ctype[0]=w.wcs.ctype[0]
    wn.wcs.ctype[1]=w.wcs.ctype[1]
    
    header = wn.to_header()
    header["NAXIS"]=2
    copy=('EQUINOX','EPOCH','BMAJ', 'BMIN', 'BPA', 'RESTFRQ', 'TELESCOP', 'OBSERVER')
    for k in copy:
        r=f[0].header.get(k)
        if r:
            header[k]=r

    slice=[]
    for i in range(naxis,0,-1):
        if i<=2:
            slice.append(np.s_[:],)
        else:
            slice.append(0)
        
    hdu = fits.PrimaryHDU(header=header,data=f[0].data[slice])
    return hdu


def find_imagenoise(workingimage,estnoise):
    f = fits.open(workingimage)
    noisearray = f[0].data.flatten()
    maxpixel = np.max(noisearray)
    noisearray = np.random.permutation(noisearray)[:10000]
    #noisepix = np.array(filter(lambda x: abs(x) > 10E-8,noisearray)) # Filter out the edge pixels which have values around 1E-10
    noisepix = np.array(filter(lambda x: abs(x)<50.0*estnoise,noisepix))
    f.close()
    rms = fit_gaussian_histogram(noisepix,'n')
    return rms

#------------------------------------------------------------

def model_gaussian(t, coeffs):
    return coeffs[0] + coeffs[1] * np.exp( - ((t-coeffs[2])**2.0/(2*coeffs[3]**2)))

#------------------------------------------------------------
def residuals_gaussian(coeffs, y, t):
    return y - model_gaussian(t, coeffs)

#------------------------------------------------------------
def fit_gaussian_histogram(pixelvals,plotting):

    fitnumbers,cellsizes = np.histogram(pixelvals,100)
    sigmaguess = np.std(pixelvals)/(abs(cellsizes[1]-cellsizes[0]))
    x0 = [0.0,max(fitnumbers),np.where(fitnumbers==max(fitnumbers))[0][0],sigmaguess] #Offset amp, amp, x-offset, sigma
    t = np.arange(len(fitnumbers))
    x, flag = scipy.optimize.leastsq(residuals_gaussian, x0, args=(fitnumbers, t))

    if plotting == 'y':
        pylab.plot(fitnumbers)
        pylab.plot(t,fitnumbers,t,model_gaussian(t,x))
        pylab.show()
        pylab.close()
        pylab.cla()

    #print 'Sigma is %s'%(x[3]*abs(cellsizes[1]-cellsizes[0]))
    
    return (x[3]*abs(cellsizes[1]-cellsizes[0]))
