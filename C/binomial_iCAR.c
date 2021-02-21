// ==============================================================================
// author          :Ghislain Vieilledent
// email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
// web             :https://ecology.ghislainv.fr
// python_version  :>=2.7
// license         :GPLv3
// ==============================================================================

// Python libraries
#include <Python.h>
#include <numpy/arrayobject.h>
// C libraries
//#include <stdio.h>  // already in Python.h
//#include <stdlib.h>  // already in Python.h
#include <math.h>
// My own functions
#include "useful.h"


/* ********************************************************************* */
/* dens_par */

struct dens_par {
  /* Data */
  int NOBS;
  int NCELL;
  int *Y;
  int *T;
  int *IdCell;
  int *nObsCell;
  int **PosCell;
  /* Spatial correlation */
  int *nNeigh;
  int **Neigh;
  int pos_rho;
  double *rho_run;
  double shape, rate;
  double Vrho_run;
  /* Suitability */
  int NP;
  int pos_beta;
  double **X;
  double *mubeta, *Vbeta;
  double *beta_run; 
};


/* ************************************************************ */
/* betadens */

static double betadens (double beta_k, void *dens_data) {
  // Pointer to the structure: d
  struct dens_par *d;
  d=dens_data;
  // Indicating the rank of the parameter of interest
  int k=d->pos_beta;
  // logLikelihood
  double logL=0.0;
  for (int n=0; n<d->NOBS; n++) {
    /* theta */
    double Xpart_theta=0.0;
    for (int p=0; p<d->NP; p++) {
      if (p!=k) {
        Xpart_theta+=d->X[n][p]*d->beta_run[p];
      }
    }
    Xpart_theta+=d->X[n][k]*beta_k;
    double theta=invlogit(Xpart_theta+d->rho_run[d->IdCell[n]]);
    /* log Likelihood */
    //logL+=mydbinom(d->Y[n],d->T[n],theta,1);
    logL+=mylndbern(d->Y[n],theta);
  }
  // logPosterior=logL+logPrior
  double logP=logL+mydnorm(beta_k,d->mubeta[k],sqrt(d->Vbeta[k]),1);
  return logP;
}


/* ************************************************************ */
/* rhodens_visited */

static double rhodens_visited (double rho_i, void *dens_data) {
  // Pointer to the structure: d 
  struct dens_par *d;
  d=dens_data;
  // Indicating the rank of the parameter of interest
  int i=d->pos_rho; //
  // logLikelihood
  double logL=0;
  for (int m=0; m<d->nObsCell[i]; m++) {
    int w=d->PosCell[i][m]; // which observation
    /* theta */
    double Xpart_theta=0.0;
    for (int p=0; p<d->NP; p++) {
      Xpart_theta+=d->X[w][p]*d->beta_run[p];
    }
    double theta=invlogit(Xpart_theta+rho_i);
    /* log Likelihood */
    //logL+=mydbinom(d->Y[w],d->T[w],theta,1);
    logL+=mylndbern(d->Y[w],theta);
  }
  // logPosterior=logL+logPrior
  int nNeighbors=d->nNeigh[i];
  double sumNeighbors=0.0;
  for (int l=0; l<nNeighbors; l++) {
    sumNeighbors+=d->rho_run[d->Neigh[i][l]];
  }
  double meanNeighbors=sumNeighbors/nNeighbors;
  double logP=logL+mydnorm(rho_i,meanNeighbors,sqrt(d->Vrho_run/nNeighbors),1); 
  return logP;
}

/* ************************************************************ */
/* rhodens_unvisited */

static double rhodens_unvisited (void *dens_data) {
  // Pointer to the structure: d 
  struct dens_par *d;
  d=dens_data;
  // Indicating the rank of the parameter of interest
  int i=d->pos_rho; //
  // Draw directly in the posterior distribution
  int nNeighbors=d->nNeigh[i];
  double sumNeighbors=0.0;
  for (int l=0; l<nNeighbors; l++) {
    sumNeighbors+=d->rho_run[d->Neigh[i][l]];
  }
  double meanNeighbors=sumNeighbors/nNeighbors;
  double sample=myrnorm(meanNeighbors,sqrt(d->Vrho_run/nNeighbors)); 
  return sample;
}

/* ************************************************************ */
/* Function for transforming C array to PyList */
static PyObject *CArray2PyList (double *CArray, int len) {
  PyObject *PythonList = PyList_New(len);
  if (!PythonList) {
    return NULL;
  }
  for (int i=0; i<len; i++) {
    PyObject *num = PyFloat_FromDouble(CArray[i]);
    if (!num) {
      Py_DECREF(PythonList);
      return NULL;
    }
    PyList_SET_ITEM(PythonList, i, num); // reference to num stolen
  }
  return PythonList;
}

/* ************************************************************ */
/* Gibbs sampler function */

static PyObject *binomial_iCAR(PyObject *self, PyObject *args, PyObject *keywds) {

  // Constants and data
  const int ngibbs; // Number of iterations, burning and samples
  const int nthin;
  const int nburn; 
  const int nobs; // Number of observations
  const int ncell; // Constants
  const int np; // Number of fixed effects for theta
  PyObject *Y_obj; // Number of successes (presences)
  PyObject *T_obj; // Number of trials
  PyObject *X_obj; // Suitability covariates
  // Spatial correlation
  PyObject *C_obj; // Cell Id
  PyObject *nNeigh_obj; // Number of neighbors for each cell
  PyObject *Neigh_obj; // Vector of neighbors sorted by cell
  // Predictions
  const int npred; // Number of predictions
  PyObject *X_pred_obj; // Suitability covariates for predictions
  PyObject *C_pred_obj; // Cell Id for predictions
  // Starting values for M-H
  PyObject *beta_start_obj;
  PyObject *rho_start_obj;
  const double Vrho_start;
  // Defining priors
  PyObject *mubeta_obj;
  PyObject *Vbeta_obj;
  const double priorVrho;
  const double shape;
  const double rate;
  const double Vrho_max;
  // Seeds
  const int seed;
  // Verbose
  const int verbose;
  // Save rho and p
  const int save_rho;
  const int save_p;

  // Keyword list
  static char *kwlist[] = {"ngibbs", "nthin", "nburn", "nobs", "ncell", "np",
                           "Y_obj", "T_obj", "X_obj",
                           "C_obj", "nNeigh_obj", "Neigh_obj",
                           "npred", "X_pred_obj", "C_pred_obj",
                           "beta_start_obj", "rho_start_obj", "Vrho_start",
                           "mubeta_obj", "Vbeta_obj", "priorVrho", "shape", "rate", "Vrho_max",
                           "seed", "verbose", "save_rho", "save_p", NULL}; // NULL sentinel
      
  // Parse arguments
  if (!PyArg_ParseTupleAndKeywords(args, keywds, "iiiiiiOOOOOOiOOOOdOOddddiiii", kwlist,
                                   &ngibbs, &nthin, &nburn, &nobs, &ncell, &np,
                                   &Y_obj, &T_obj, &X_obj,
                                   &C_obj, &nNeigh_obj, &Neigh_obj,
                                   &npred, &X_pred_obj, &C_pred_obj,
                                   &beta_start_obj, &rho_start_obj, &Vrho_start,
                                   &mubeta_obj, &Vbeta_obj, &priorVrho, &shape, &rate, &Vrho_max,
                                   &seed, &verbose, &save_rho, &save_p)) {
    return NULL;
  }

  // Interpret the input Python objects as Numpy arrays
  PyObject *Y_array = PyArray_FROM_OTF(Y_obj, NPY_INT32, NPY_IN_ARRAY);
  PyObject *T_array = PyArray_FROM_OTF(T_obj, NPY_INT32, NPY_IN_ARRAY);
  PyObject *X_array = PyArray_FROM_OTF(X_obj, NPY_FLOAT64, NPY_IN_ARRAY);
  PyObject *C_array = PyArray_FROM_OTF(C_obj, NPY_INT32, NPY_IN_ARRAY);
  PyObject *nNeigh_array = PyArray_FROM_OTF(nNeigh_obj, NPY_INT32, NPY_IN_ARRAY);
  PyObject *Neigh_array = PyArray_FROM_OTF(Neigh_obj, NPY_INT32, NPY_IN_ARRAY);
  PyObject *X_pred_array = PyArray_FROM_OTF(X_pred_obj, NPY_FLOAT64, NPY_IN_ARRAY);
  PyObject *C_pred_array = PyArray_FROM_OTF(C_pred_obj, NPY_INT32, NPY_IN_ARRAY);
  PyObject *beta_start_array = PyArray_FROM_OTF(beta_start_obj, NPY_FLOAT64, NPY_IN_ARRAY);
  PyObject *rho_start_array = PyArray_FROM_OTF(rho_start_obj, NPY_FLOAT64, NPY_IN_ARRAY);
  PyObject *mubeta_array = PyArray_FROM_OTF(mubeta_obj, NPY_FLOAT64, NPY_IN_ARRAY);
  PyObject *Vbeta_array = PyArray_FROM_OTF(Vbeta_obj, NPY_FLOAT64, NPY_IN_ARRAY);

  // If that didn't work, throw an exception
  if (Y_array == NULL || T_array == NULL || X_array == NULL || C_array == NULL || nNeigh_array == NULL ||
      Neigh_array == NULL || X_pred_array == NULL || C_pred_array == NULL || beta_start_array == NULL ||
      rho_start_array == NULL || mubeta_array == NULL || Vbeta_array == NULL) {
    Py_XDECREF(Y_array);
    Py_XDECREF(T_array);
    Py_XDECREF(X_array);
    Py_XDECREF(C_array);
    Py_XDECREF(nNeigh_array);
    Py_XDECREF(Neigh_array);
    Py_XDECREF(X_pred_array);
    Py_XDECREF(C_pred_array);
    Py_XDECREF(beta_start_array);
    Py_XDECREF(rho_start_array);
    Py_XDECREF(mubeta_array);
    Py_XDECREF(Vbeta_array);
    return NULL;
  }

  // Get pointers to the data as C-types
  int *Y_vect = (int*)PyArray_DATA(Y_array);
  int *T_vect = (int*)PyArray_DATA(T_array);
  double *X_vect = (double*)PyArray_DATA(X_array);
  int *C_vect = (int*)PyArray_DATA(C_array);
  int *nNeigh_vect = (int*)PyArray_DATA(nNeigh_array);
  int *Neigh_vect = (int*)PyArray_DATA(Neigh_array);
  double *X_pred_vect = (double*)PyArray_DATA(X_pred_array);
  int *C_pred_vect = (int*)PyArray_DATA(C_pred_array);
  double *beta_start_vect = (double*)PyArray_DATA(beta_start_array);
  double *rho_start_vect = (double*)PyArray_DATA(rho_start_array);
  double *mubeta_vect = (double*)PyArray_DATA(mubeta_array);
  double *Vbeta_vect = (double*)PyArray_DATA(Vbeta_array);
  
  ////////////////////////////////////////////////////////////////////////////////
  //%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  // Defining and initializing objects

  ////////////////////////////////////////
  // Initialize random number generator //
  srand(seed);

  ///////////////////////////
  // Redefining constants //
  const int NGIBBS=ngibbs;
  const int NTHIN=nthin;
  const int NBURN=nburn;
  const int NSAMP=(NGIBBS-NBURN)/NTHIN;
  const int NOBS=nobs;
  const int NCELL=ncell;
  const int NP=np;
  const int NPRED=npred;

  ///////////////////////////////////
  // Declaring some useful objects //
  double *theta_run=malloc(NOBS*sizeof(double));
  for (int n=0; n<NOBS; n++) {
    theta_run[n]=0.0;
  }
  double *theta_pred_run=malloc(NPRED*sizeof(double));
  for (int m=0; m<NPRED; m++) {
    theta_pred_run[m]=0.0;
  }

  //////////////////////////////////////////////////////////
  // Set up and initialize structure for density function //
  struct dens_par dens_data;

  /* Data */
  dens_data.NOBS=NOBS;
  dens_data.NCELL=NCELL;
  // Y
  dens_data.Y=malloc(NOBS*sizeof(int));
  for (int n=0; n<NOBS; n++) {
    dens_data.Y[n]=Y_vect[n];
  }
  // T
  dens_data.T=malloc(NOBS*sizeof(int));
  for (int n=0; n<NOBS; n++) {
    dens_data.T[n]=T_vect[n];
  }

  /* Spatial correlation */
  // IdCell
  dens_data.IdCell=malloc(NOBS*sizeof(int));
  for (int n=0; n<NOBS; n++) {
    dens_data.IdCell[n]=C_vect[n];
  }
  // nObsCell
  dens_data.nObsCell=malloc(NCELL*sizeof(int));
  for (int i=0; i<NCELL; i++) {
    dens_data.nObsCell[i]=0;
    for (int n=0; n<NOBS; n++) {
      if (dens_data.IdCell[n]==i) {
        dens_data.nObsCell[i]++;
      }
    }
  }
  // PosCell
  dens_data.PosCell=malloc(NCELL*sizeof(int*));
  for (int i=0; i<NCELL; i++) {
    dens_data.PosCell[i]=malloc(dens_data.nObsCell[i]*sizeof(int));
    int repCell=0;
    for (int n=0; n<NOBS; n++) {
      if (dens_data.IdCell[n]==i) {
        dens_data.PosCell[i][repCell]=n;
        repCell++;
      }
    }
  }
  // Number of neighbors by cell
  dens_data.nNeigh=malloc(NCELL*sizeof(int));
  for (int i=0; i<NCELL; i++) {
    dens_data.nNeigh[i]=nNeigh_vect[i];
  }
  // Neighbor identifiers by cell
  int posNeigh=0;
  dens_data.Neigh=malloc(NCELL*sizeof(int*));
  for (int i=0; i<NCELL; i++) {
    dens_data.Neigh[i]=malloc(nNeigh_vect[i]*sizeof(int));
    for (int m=0; m<nNeigh_vect[i]; m++) {
      dens_data.Neigh[i][m]=Neigh_vect[posNeigh+m];
    }
    posNeigh+=nNeigh_vect[i];
  }
  dens_data.pos_rho=0;
  dens_data.rho_run=malloc(NCELL*sizeof(double));
  for (int i=0; i<NCELL; i++) {
    dens_data.rho_run[i]=rho_start_vect[i];
  }
  dens_data.shape=shape;
  dens_data.rate=rate;
  dens_data.Vrho_run=Vrho_start;

  /* Suitability process */
  dens_data.NP=NP;
  dens_data.pos_beta=0;
  dens_data.X=malloc(NOBS*sizeof(double*));
  for (int n=0; n<NOBS; n++) {
    dens_data.X[n]=malloc(NP*sizeof(double));
    for (int p=0; p<NP; p++) {
      dens_data.X[n][p]=X_vect[p*NOBS+n];
    }
  }
  dens_data.mubeta=malloc(NP*sizeof(double));
  dens_data.Vbeta=malloc(NP*sizeof(double));
  for (int p=0; p<NP; p++) {
    dens_data.mubeta[p]=mubeta_vect[p];
    dens_data.Vbeta[p]=Vbeta_vect[p];
  }
  dens_data.beta_run=malloc(NP*sizeof(double));
  for (int p=0; p<NP; p++) {
    dens_data.beta_run[p]=beta_start_vect[p];
  }

  /* Visited cell or not */
  int *viscell = malloc(NCELL*sizeof(int));
  for (int i=0; i<NCELL; i++) {
    viscell[i]=0;
  }
  for (int n=0; n<NOBS; n++) {
    viscell[dens_data.IdCell[n]]++;
  }
  int NVISCELL=0;
  for (int i=0; i<NCELL; i++) {
    if (viscell[i]>0) {
      NVISCELL++;
    }
  }

  /* Predictions */
  // IdCell_pred
  int *IdCell_pred=malloc(NPRED*sizeof(int));
  for (int m=0; m<NPRED; m++) {
    IdCell_pred[m]=C_pred_vect[m];
  }
  // X_pred
  double **X_pred=malloc(NPRED*sizeof(double*));
  for (int m=0; m<NPRED; m++) {
    X_pred[m]=malloc(NP*sizeof(double));
    for (int p=0; p<NP; p++) {
      X_pred[m][p]=X_pred_vect[p*NPRED+m];
    }
  }

  /* Parameters to save */
  // beta_vect
  double *beta_vect=malloc(NP*NSAMP*sizeof(double));
  for (int i=0; i<(NP*NSAMP); i++) {
    beta_vect[i]=0.0;
  }
  // Vrho_vect
  double *Vrho_vect=malloc(NSAMP*sizeof(double));
  for (int i=0; i<NSAMP; i++) {
    Vrho_vect[i]=0.0;
  }
  // rho_vect
  double *rho_vect;
  if (save_rho==0) {
    rho_vect=malloc(NCELL*sizeof(double));
    for (int i=0; i<NCELL; i++) {
      rho_vect[i]=0.0;
    }
  }
  else {
    rho_vect=malloc(NCELL*NSAMP*sizeof(double));
    for (int i=0; i<(NCELL*NSAMP); i++) {
      rho_vect[i]=0.0;
    }
  }
      
  /* Diagnostic */
  // Deviance
  double *Deviance_vect=malloc(NSAMP*sizeof(double));
  for (int i=0; i<NSAMP; i++) {
    Deviance_vect[i]=0.0;
  }
  // theta_latent
  double *theta_latent_vect=malloc(NOBS*sizeof(double));
  for (int i=0; i<NOBS; i++) {
    theta_latent_vect[i]=0.0;
  }
  // theta_pred_vect
  double *theta_pred_vect;
  if (save_p==0) {
    theta_pred_vect=malloc(NPRED*sizeof(double));
    for (int i=0; i<NPRED; i++) {
      theta_pred_vect[i]=0.0;
    }
  }
  else {
    theta_pred_vect=malloc(NPRED*NSAMP*sizeof(double));
    for (int i=0; i<(NPRED*NSAMP); i++) {
      theta_pred_vect[i]=0.0;
    }
  }

    
  ////////////////////////////////////////////////////////////
  // Proposal variance and acceptance for adaptive sampling //

  // beta
  double *sigmap_beta = malloc(NP*sizeof(double));
  int *nA_beta = malloc(NP*sizeof(int));
  double *Ar_beta = malloc(NP*sizeof(double)); // Acceptance rate 
  for (int p=0; p<NP; p++) {
    nA_beta[p]=0;
    sigmap_beta[p]=1.0;
    Ar_beta[p]=0.0;
  }

  // rho
  double *sigmap_rho = malloc(NCELL*sizeof(double));
  int *nA_rho = malloc(NCELL*sizeof(int));
  double *Ar_rho = malloc(NCELL*sizeof(double)); // Acceptance rate 
  for (int i=0; i<NCELL; i++) {
    nA_rho[i]=0;
    sigmap_rho[i]=1.0;
    Ar_rho[i]=0.0;
  }
 
  ////////////
  // Message//
  printf("\nRunning the Gibbs sampler. It may be long, please keep cool :)\n\n");
  //R_FlushConsole();
  //R_ProcessEvents(); for windows

  ///////////////////////////////////////////////////////////////////////////////////////
  //%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
  // Gibbs sampler

  for (int g=0; g<NGIBBS; g++) {


    ////////////////////////////////////////////////
    // beta
	
    for (int p=0; p<NP; p++) {
      dens_data.pos_beta=p; // Specifying the rank of the parameter of interest
      double x_now=dens_data.beta_run[p];
      double x_prop=myrnorm(x_now,sigmap_beta[p]);
      double p_now=betadens(x_now, &dens_data);
      double p_prop=betadens(x_prop, &dens_data);
      double r=exp(p_prop-p_now); // ratio
      double z=myrunif();
      // Actualization
      if (z < r) {
        dens_data.beta_run[p]=x_prop;
        nA_beta[p]++;
      }
    }


    ////////////////////////////////////////////////
    // rho
	
    /* Sampling rho_run[i] */
    for (int i=0; i<NCELL; i++) {
      dens_data.pos_rho=i; // Specifying the rank of the parameter of interest
      if (viscell[i]>0) {
        double x_now=dens_data.rho_run[i];
        double x_prop=myrnorm(x_now,sigmap_rho[i]);
        double p_now=rhodens_visited(x_now, &dens_data);
        double p_prop=rhodens_visited(x_prop, &dens_data);
        double r=exp(p_prop-p_now); // ratio
        double z=myrunif();
        // Actualization
        if (z < r) {
          dens_data.rho_run[i]=x_prop;
          nA_rho[i]++;
        }
      }
      else {
        dens_data.rho_run[i]=rhodens_unvisited(&dens_data);
      }
    }

    /* Centering rho_run[i] */
    double rho_sum=0.0;
    for (int i=0; i<NCELL; i++) {
      rho_sum+=dens_data.rho_run[i];
    }
    double rho_bar=rho_sum/NCELL;
    for (int i=0; i<NCELL; i++) {
      dens_data.rho_run[i]=dens_data.rho_run[i]-rho_bar;
    }


    ////////////////////////////////////////////////
    // Vrho
	
    if (priorVrho>0.0) { // fixed value for Vrho
      dens_data.Vrho_run=priorVrho;
    }
    else {
      double Sum=0.0;
      for (int i=0; i<NCELL; i++) {
        double Sum_neigh=0.0;
        double nNeigh=dens_data.nNeigh[i];
        double rho_run=dens_data.rho_run[i];
        for (int m=0; m<nNeigh; m++) {
          Sum_neigh += dens_data.rho_run[dens_data.Neigh[i][m]];
        }
        Sum += rho_run*(nNeigh*rho_run-Sum_neigh);
      }
      if (priorVrho==-1.0) { // prior = 1/Gamma(shape,rate)
        double Shape=shape+0.5*(NCELL-1);
        double Rate=rate+0.5*Sum;
        dens_data.Vrho_run=Rate/myrgamma1(Shape);
      }
      if (priorVrho==-2.0) { // prior = Uniform(0,Vrho_max)
        double Shape=0.5*NCELL-1;
        double Rate=0.5*Sum;
        dens_data.Vrho_run=1/myrtgamma_left(Shape,Rate,1/Vrho_max);
      }
    }


    //////////////////////////////////////////////////
    // Deviance

    // logLikelihood
    double logL=0.0;
    for (int n=0; n<NOBS; n++) {
      /* theta */
      double Xpart_theta=0.0;
      for (int p=0; p<NP; p++) {
        Xpart_theta+=dens_data.X[n][p]*dens_data.beta_run[p];
      }
      theta_run[n]=invlogit(Xpart_theta+dens_data.rho_run[dens_data.IdCell[n]]);
      /* log Likelihood */
      //logL+=mydbinom(dens_data.Y[n],dens_data.T[n],theta_run[n],1);
      logL+=mylndbern(dens_data.Y[n],theta_run[n]);
    }

    // Deviance
    double Deviance_run=-2*logL;


    //////////////////////////////////////////////////
    // Predictions
    for (int m=0; m<NPRED; m++) {
      /* theta_pred_run */
      double Xpart_theta_pred=0.0;
      for (int p=0; p<NP; p++) {
        Xpart_theta_pred+=X_pred[m][p]*dens_data.beta_run[p];
      }
      theta_pred_run[m]=invlogit(Xpart_theta_pred+dens_data.rho_run[IdCell_pred[m]]);
    }


    //////////////////////////////////////////////////
    // Output
    if (((g+1)>NBURN) && (((g+1)%(NTHIN))==0)) {
      int isamp=((g+1)-NBURN)/(NTHIN);
      // beta
      for (int p=0; p<NP; p++) {
        beta_vect[p*NSAMP+(isamp-1)]=dens_data.beta_run[p];
      }
      // rho
      if (save_rho==0) { // We compute the mean of NSAMP values
        for (int i=0; i<NCELL; i++) {
          rho_vect[i]+=dens_data.rho_run[i]/NSAMP; 
        }
      }
      if (save_rho==1) { // The NSAMP sampled values for rhos are saved
        for (int i=0; i<NCELL; i++) {
          rho_vect[i*NSAMP+(isamp-1)]=dens_data.rho_run[i]; 
        }
      }
      // Vrho
      Vrho_vect[isamp-1]=dens_data.Vrho_run;
      // Deviance
      Deviance_vect[isamp-1]=Deviance_run;
      // theta_latent
      for (int n=0; n<NOBS; n++) {
        theta_latent_vect[n]+=theta_run[n]/NSAMP; // We compute the mean of NSAMP values
      }
      // theta_pred
      if (save_p==0) { // We compute the mean of NSAMP values
        for (int m=0; m<NPRED; m++) {
          theta_pred_vect[m]+=theta_pred_run[m]/NSAMP; 
        }
      }
      if (save_p==1) { // The NSAMP sampled values for theta are saved
        for (int m=0; m<NPRED; m++) {
          theta_pred_vect[m*NSAMP+(isamp-1)]=theta_pred_run[m]; 
        }
      }
    }


    ///////////////////////////////////////////////////////
    // Adaptive sampling (on the burnin period)
    const double ropt=0.44; // 0.234;
    int DIV=0;
    if (NGIBBS >=1000) DIV=100;
    else DIV=NGIBBS/10;
    /* During the burnin period */
    if ((g+1)%DIV==0 && (g+1)<=NBURN) {
      // beta
      for (int p=0; p<NP; p++) {
        Ar_beta[p]=((double) nA_beta[p])/DIV;
        if (Ar_beta[p]>=ropt) sigmap_beta[p]=sigmap_beta[p]*(2-(1-Ar_beta[p])/(1-ropt));
        else sigmap_beta[p]=sigmap_beta[p]/(2-Ar_beta[p]/ropt);
        nA_beta[p]=0.0; // We reinitialize the number of acceptance to zero
      }
      // rho
      for (int i=0; i<NCELL; i++) {
        if (viscell[i]>0) {
          Ar_rho[i]=((double) nA_rho[i])/DIV;
          if (Ar_rho[i]>=ropt) sigmap_rho[i]=sigmap_rho[i]*(2-(1-Ar_rho[i])/(1-ropt));
          else sigmap_rho[i]=sigmap_rho[i]/(2-Ar_rho[i]/ropt);
          nA_rho[i]=0.0; // We reinitialize the number of acceptance to zero
        }
      }
    }
    /* After the burnin period */
    if ((g+1)%DIV==0 && (g+1)>NBURN) {
      // beta
      for (int p=0; p<NP; p++) {
        Ar_beta[p]=((double) nA_beta[p])/DIV;
        nA_beta[p]=0.0; // We reinitialize the number of acceptance to zero
      }
      // rho
      for (int i=0; i<NCELL; i++) {
        if (viscell[i]>0) {
          Ar_rho[i]=((double) nA_rho[i])/DIV;
          nA_rho[i]=0.0; // We reinitialize the number of acceptance to zero
        }
      }
    }

    
    //////////////////////////////////////////////////
    // Progress bar
    double Perc=100*(g+1)/(NGIBBS);
    if (((g+1)%(NGIBBS/100))==0 && verbose==1) {
      printf("*");
      fflush(stdout);
      //R_FlushConsole();
      //R_ProcessEvents(); for windows
      if (((g+1)%(NGIBBS/10))==0) {
        double mAr_beta=0; // Mean acceptance rate
        double mAr_rho=0;
        // beta
        for (int p=0; p<NP; p++) {
          mAr_beta+=Ar_beta[p]/NP;
        }
        // rho
        for (int i=0; i<NCELL; i++) {
          if (viscell[i]>0) {
            mAr_rho+=Ar_rho[i]/NVISCELL;
          }
        }
        printf(":%.1f%%, mean accept. rates= beta:%.3f, rho:%.3f\n",Perc,mAr_beta,mAr_rho);
        //R_FlushConsole();
        //R_ProcessEvents(); for windows
      }
    }


    //////////////////////////////////////////////////
    // User interrupt
    //R_CheckUserInterrupt(); // allow user interrupt 	    
	
  } // Gibbs sampler


  ///////////////
  // Delete memory allocation (see malloc())
  /* Data */
  free(dens_data.Y);
  free(dens_data.T);
  free(dens_data.IdCell);
  free(dens_data.nObsCell);
  for (int i=0; i<NCELL; i++) {
    free(dens_data.PosCell[i]);
  }
  free(dens_data.PosCell);
  /* Spatial correlation */
  free(dens_data.nNeigh);
  for (int i=0; i<NCELL; i++) {
    free(dens_data.Neigh[i]);
  }
  free(dens_data.Neigh);
  free(dens_data.rho_run);
  /* Suitability */
  for (int n=0; n<NOBS; n++) {
    free(dens_data.X[n]);
  }
  free(dens_data.X);
  free(dens_data.mubeta);
  free(dens_data.Vbeta);
  free(dens_data.beta_run);
  free(theta_run);
  /* Visited cells */
  free(viscell);
  /* Predictions */
  free(IdCell_pred);
  for (int m=0; m<NPRED; m++) {
    free(X_pred[m]);
  }
  free(X_pred);
  free(theta_pred_run);
  /* Adaptive MH */
  free(sigmap_beta);
  free(nA_beta);
  free(Ar_beta);
  free(sigmap_rho);
  free(nA_rho);
  free(Ar_rho);

  // Delete memory allocation: remove Python Numpy array
  Py_XDECREF(Y_array);
  Py_XDECREF(T_array);
  Py_XDECREF(X_array);
  Py_XDECREF(C_array);
  Py_XDECREF(nNeigh_array);
  Py_XDECREF(Neigh_array);
  Py_XDECREF(X_pred_array);
  Py_XDECREF(C_pred_array);
  Py_XDECREF(beta_start_array);
  Py_XDECREF(rho_start_array);
  Py_XDECREF(mubeta_array);
  Py_XDECREF(Vbeta_array);

  // Return Python objects
  // Parameters to save
  PyObject *beta_obj = CArray2PyList(beta_vect, NP*NSAMP);
  PyObject *rho_obj;
  if (save_rho==0) {
    rho_obj = CArray2PyList(rho_vect, NCELL);
  }
  else {
    rho_obj = CArray2PyList(rho_vect, NCELL*NSAMP);
  }
  PyObject *Vrho_obj = CArray2PyList(Vrho_vect, NSAMP); 
  // Diagnostic
  PyObject *Deviance_obj = CArray2PyList(Deviance_vect, NSAMP);
  PyObject *theta_latent_obj = CArray2PyList(theta_latent_vect, NOBS);
  PyObject *theta_pred_obj;
  if (save_p==0) {
    theta_pred_obj = CArray2PyList(theta_pred_vect, NPRED);
  }
  else {
    theta_pred_obj = CArray2PyList(theta_pred_vect, NPRED*NSAMP);
  }
  // PyTuple
  PyObject *result_obj = PyTuple_New(6);
  PyTuple_SetItem(result_obj, 0, beta_obj);
  PyTuple_SetItem(result_obj, 1, rho_obj);
  PyTuple_SetItem(result_obj, 2, Vrho_obj);
  PyTuple_SetItem(result_obj, 3, Deviance_obj);
  PyTuple_SetItem(result_obj, 4, theta_latent_obj);
  PyTuple_SetItem(result_obj, 5, theta_pred_obj);
  
  // Return result
  return result_obj;

  // Delete memory allocation: remove Python Numpy array
  Py_XDECREF(beta_obj);
  Py_XDECREF(rho_obj);
  Py_XDECREF(Vrho_obj);
  Py_XDECREF(Deviance_obj);
  Py_XDECREF(theta_latent_obj);
  Py_XDECREF(theta_pred_obj);

  // Delete memory allocation
  free(beta_vect);
  free(rho_vect);
  free(Vrho_vect);
  free(Deviance_vect);
  free(theta_latent_vect);
  free(theta_pred_vect);
  
} // end binomial_iCAR function

/* Bind Python function names to our C functions */
static PyMethodDef hbm_methods[] = {
  /* The cast of the function is necessary since PyCFunction values
   * only take two PyObject* parameters, and binomial_iCAR() takes
   * three.
   */
  {"binomial_iCAR", (PyCFunction)binomial_iCAR, METH_VARARGS | METH_KEYWORDS,
   "Fit a Binomial linear model with iCAR process. This function encapsulates a Gibbs sampler written in C code and using a Metropolis algorithm. It is called by the function ``.model.binomial_iCAR()``."},
  {NULL, NULL, 0, NULL}  /* Sentinel */
};

/* Migrating C extensions */
/* https://stackoverflow.com/questions/43621948/c-python-module-import-error-undefined-symbol-py-initmodule3-py-initmodu?noredirect=1&lq=1 */
/* http://python3porting.com/cextensions.html */
#if PY_MAJOR_VERSION >= 3
  static struct PyModuleDef hbm = {
      PyModuleDef_HEAD_INIT,
      "hbm", /* m_name */
      "Fit hierarchical Bayesian models. This modules includes functions written in C to maximise computation efficiency.", /* m_doc */
      -1, /* m_size */
      hbm_methods, /* m_methods */
      NULL, /* m_reload */
      NULL, /* m_traverse */
      NULL, /* m_clear */
      NULL, /* m_free */
  };
#endif

/* Python calls this to let us initialize our module */
#if PY_MAJOR_VERSION < 3
  PyMODINIT_FUNC inithbm(void) {
    (void) Py_InitModule("hbm", hbm_methods);
    /* Load 'numpy' functionality. */
    import_array();
  }
#else
  PyMODINIT_FUNC PyInit_hbm(void) {
    /* Load 'numpy' functionality. */
    import_array();
    return PyModule_Create(&hbm);
  }
#endif

// End
