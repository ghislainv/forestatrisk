// ==============================================================================
// author          :Ghislain Vieilledent
// email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
// web             :https://ecology.ghislainv.fr
// python_version  :2.7
// license         :GPLv3
// ==============================================================================

/* Include */
#include <stdlib.h> // For rand(), RAND_MAX and exit
#include <stdio.h> // For fprintf and stderr
#include <math.h>
#include "useful.h" // To include function prototypes

/* Some definitions that aren't in math.h */
#ifndef M_PI
#define M_PI 3.141592653589793238462643383280  /* pi */
#endif
#define M_LN_2PI 1.837877066409345483560659472811  /* log(2*pi) */
#define M_LN_SQRT_2PI 0.918938533204672741780329736406  /* log(sqrt(2*pi)) == log(2*pi)/2 */
#define M_LN_SQRT_PId2  0.225791352644727432363097614947  /* log(sqrt(pi/2)) == log(pi/2)/2 */
#define M_1_SQRT_2PI  0.39894228040143267793994605993  /* 1/sqrt(2*pi) */
#define M_2PI   6.28318530717958647692528676655  /* 2*pi */

/* Define static functions */
static double chebyshev_eval (double x, const double *a, int n);
static double lngammacor(double x);
static double bd0(double x, double np);
static double gammafn (double x);
static double lngammafn(double x);
static double stirlerr(double n);
static double dbinom_raw (double x, double n, double p, double q, int l);

/*****************************************************************/
/* General functions */
/*****************************************************************/

/******************/
/* Function logit */
double logit (double x) {
    double Result=log(x)-log(1-x);
    return Result;
}

/*********************/
/* Function invlogit */
double invlogit (double x) {
    if (x > 0) {
        return 1/(1+exp(-x));
    }
    else {
	return exp(x)/(1+exp(x));
    }
}

/************************************************************/
/* Helper functions for Binomial distribution */
/* Adapted from Scythe */

/* ********************************************* */
/* Evaluate a Chebysheve series at a given point */
static double chebyshev_eval (double x, const double *a, int n) {

  if (n < 1 || n > 1000) {
    fprintf(stderr, "n not on [1, 1000]\n");
    exit(EXIT_FAILURE);
  }
  if (x < -1.1 || x > 1.1) {
    fprintf(stderr, "x not on [-1.1, 1.1]\n");
    exit(EXIT_FAILURE);
  }
      
  double b0, b1, b2;
  b0 = b1 = b2 = 0;
  
  double twox = x * 2;
  
  for (int i = 1; i <= n; ++i) {
    b2 = b1;
    b1 = b0;
    b0 = twox * b1 - b2 + a[n - i];
  }
  
  return (b0 - b2) * 0.5;
}

/* **************************************************** */
/* Computes the log gamma correction factor for x >= 10 */
static double lngammacor(double x) {
  const static double algmcs[5] = {
    +.1666389480451863247205729650822e+0,
    -.1384948176067563840732986059135e-4,
    +.9810825646924729426157171547487e-8,
    -.1809129475572494194263306266719e-10,
    +.6221098041892605227126015543416e-13,
  };
  if (x < 10) {
    fprintf(stderr, "This function requires x >= 10");
    exit(EXIT_FAILURE);
  }
  if (x >= 3.745194030963158e306) {
    fprintf(stderr, "Underflow");
    exit(EXIT_FAILURE);
  }          
  if (x < 94906265.62425156) {
    double tmp = 10 / x;
    return chebyshev_eval(tmp * tmp * 2 - 1, algmcs, 5) / x;
  }
      
  return 1 / (x * 12);
}

/* ***************************** */
/* Evaluates the "deviance part" */
static double bd0(double x, double np) {
  double ej, s, s1, v;
  if (fabs(x-np) < 0.1*(x+np)) {
    v = (x-np)/(x+np);
    s = (x-np)*v;
    ej = 2*x*v;
    v = v*v;
    for (int j=1; ; j++) { /* Taylor series */
      ej *= v;
      s1 = s+ej/((j<<1)+1);
      if (s1==s) /* last term was effectively 0 */
        return(s1);
      s = s1;
    }
  }
  /* else:  | x - np |  is not too small */
  return(x*log(x/np)+np-x);
}

/* ************** */
/* Gamma function */
static double gammafn (double x) {
  
  const double gamcs[22] = {
    +.8571195590989331421920062399942e-2,
    +.4415381324841006757191315771652e-2,
    +.5685043681599363378632664588789e-1,
    -.4219835396418560501012500186624e-2,
    +.1326808181212460220584006796352e-2,
    -.1893024529798880432523947023886e-3,
    +.3606925327441245256578082217225e-4,
    -.6056761904460864218485548290365e-5,
    +.1055829546302283344731823509093e-5,
    -.1811967365542384048291855891166e-6,
    +.3117724964715322277790254593169e-7,
    -.5354219639019687140874081024347e-8,
    +.9193275519859588946887786825940e-9,
    -.1577941280288339761767423273953e-9,
    +.2707980622934954543266540433089e-10,
    -.4646818653825730144081661058933e-11,
    +.7973350192007419656460767175359e-12,
    -.1368078209830916025799499172309e-12,
    +.2347319486563800657233471771688e-13,
    -.4027432614949066932766570534699e-14,
    +.6910051747372100912138336975257e-15,
    -.1185584500221992907052387126192e-15,
  };

  double y = fabs(x);

  if (y <= 10) {

    /* Compute gamma(x) for -10 <= x <= 10
     * Reduce the interval and find gamma(1 + y) for 0 <= y < 1
     * first of all. */

    int n = (int) x;
    if (x < 0)
      --n;
      
    y = x - n;  /* n = floor(x)  ==>  y in [ 0, 1 ) */
    --n;
    double value = chebyshev_eval(y * 2 - 1, gamcs, 22) + .9375;
      
    if (n == 0)
      return value;  /* x = 1.dddd = 1+y */

    if (n < 0) {
      /* compute gamma(x) for -10 <= x < 1 */

      /* If the argument is exactly zero or a negative integer */
      /* then return NaN. */
      if (x == 0 || (x < 0 && x == n + 2)) {
        fprintf(stderr, "x is 0 or a negative integer");
        exit(EXIT_FAILURE);
      }

      /* The answer is less than half precision */
      /* because x too near a negative integer. */
      if (x < -0.5 && fabs((x - (int)(x - 0.5)) / x) < 67108864.0) {
        fprintf(stderr, "Answer < 1/2 precision because x is too near a negative integer");
        exit(EXIT_FAILURE);
      }

      /* The argument is so close to 0 that the result would overflow. */
      if (y < 2.2474362225598545e-308) {
        fprintf(stderr, "x too close to 0");
        exit(EXIT_FAILURE);
      }

      n = -n;

      for (int i = 0; i < n; i++)
        value /= (x + i);
        
      return value;
    }
      
    else {
      /* gamma(x) for 2 <= x <= 10 */
      for (int i = 1; i <= n; i++) {
        value *= (y + i);
      }
      return value;
    }
      
  }
    
  else {
    /* gamma(x) for   y = |x| > 10. */

    /* Overflow */
    if (x > 171.61447887182298) { 
      fprintf(stderr, "Overflow");
      exit(EXIT_FAILURE);
    }

    /* Underflow */
    if (x < -170.5674972726612) {
      fprintf(stderr, "Underflow");
      exit(EXIT_FAILURE);
    }

    double value = exp((y - 0.5) * log(y) - y 
                       + M_LN_SQRT_2PI + lngammacor(y));

    if (x > 0)
      return value;

    if (fabs((x - (int)(x - 0.5))/x) < 67108864.0) {
      fprintf(stderr, "Answer < 1/2 precision because x is too near a negative integer");
      exit(EXIT_FAILURE);
    }

    double sinpiy = sin(M_PI * y);

    /* Negative integer arg - overflow */
    if (sinpiy == 0) {
      fprintf(stderr, "Overflow");
      exit(EXIT_FAILURE);
    }

    return -M_PI / (y * sinpiy * value);
  }
}

/* The natural log of the absolute value of the gamma function */
static double lngammafn(double x) {
  if (x <= 0 && x == (int) x) {
    fprintf(stderr, "x is 0 or a negative integer");
    exit(EXIT_FAILURE);
  }

  double y = fabs(x);

  if (y <= 10)
    return log(fabs(gammafn(x)));

  if (y > 2.5327372760800758e+305) {
    fprintf(stderr, "Overflow");
    exit(EXIT_FAILURE);
  }

  if (x > 0)  /* i.e. y = x > 10 */
    return M_LN_SQRT_2PI + (x - 0.5) * log(x) - x + lngammacor(x);
    
  /* else: x < -10; y = -x */
  double sinpiy = fabs(sin(M_PI * y));

  if (sinpiy == 0) {  /* Negative integer argument */
    fprintf(stderr, "UNEXPECTED ERROR: Should never happen!");
    exit(EXIT_FAILURE);
  }

  double ans = M_LN_SQRT_PId2 + (x - 0.5) * log(y) - x - log(sinpiy) - lngammacor(y);

  if (fabs((x - (int)(x - 0.5)) * ans / x) < 1.490116119384765696e-8) {
    fprintf(stderr, "Answer < 1/2 precision because x is too near a negative integer");
    exit(EXIT_FAILURE);
  }
  return ans;
}

/* Computes the log of the error term in Stirling's formula */
static double stirlerr(double n) {
#define S0 0.083333333333333333333       /* 1/12 */
#define S1 0.00277777777777777777778     /* 1/360 */
#define S2 0.00079365079365079365079365  /* 1/1260 */
#define S3 0.000595238095238095238095238 /* 1/1680 */
#define S4 0.0008417508417508417508417508/* 1/1188 */
      
  /* error for 0, 0.5, 1.0, 1.5, ..., 14.5, 15.0 */
  const static double sferr_halves[31] = {
    0.0, /* n=0 - wrong, place holder only */
    0.1534264097200273452913848,  /* 0.5 */
    0.0810614667953272582196702,  /* 1.0 */
    0.0548141210519176538961390,  /* 1.5 */
    0.0413406959554092940938221,  /* 2.0 */
    0.03316287351993628748511048, /* 2.5 */
    0.02767792568499833914878929, /* 3.0 */
    0.02374616365629749597132920, /* 3.5 */
    0.02079067210376509311152277, /* 4.0 */
    0.01848845053267318523077934, /* 4.5 */
    0.01664469118982119216319487, /* 5.0 */
    0.01513497322191737887351255, /* 5.5 */
    0.01387612882307074799874573, /* 6.0 */
    0.01281046524292022692424986, /* 6.5 */
    0.01189670994589177009505572, /* 7.0 */
    0.01110455975820691732662991, /* 7.5 */
    0.010411265261972096497478567, /* 8.0 */
    0.009799416126158803298389475, /* 8.5 */
    0.009255462182712732917728637, /* 9.0 */
    0.008768700134139385462952823, /* 9.5 */
    0.008330563433362871256469318, /* 10.0 */
    0.007934114564314020547248100, /* 10.5 */
    0.007573675487951840794972024, /* 11.0 */
    0.007244554301320383179543912, /* 11.5 */
    0.006942840107209529865664152, /* 12.0 */
    0.006665247032707682442354394, /* 12.5 */
    0.006408994188004207068439631, /* 13.0 */
    0.006171712263039457647532867, /* 13.5 */
    0.005951370112758847735624416, /* 14.0 */
    0.005746216513010115682023589, /* 14.5 */
    0.005554733551962801371038690  /* 15.0 */
  };

  double nn;

  if (n <= 15.0) {
    nn = n + n;
    if (nn == (int)nn) return(sferr_halves[(int)nn]);
    return(lngammafn(n + 1.) - (n + 0.5)*log(n) + n - M_LN_SQRT_2PI);
  }

  nn = n*n;
  if (n>500) return((S0-S1/nn)/n);
  if (n> 80) return((S0-(S1-S2/nn)/nn)/n);
  if (n> 35) return((S0-(S1-(S2-S3/nn)/nn)/nn)/n);
  /* 15 < n <= 35 : */
  return((S0-(S1-(S2-(S3-S4/nn)/nn)/nn)/nn)/n);
  
#undef S0
#undef S1
#undef S2
#undef S3
#undef S4
}

/*****************************************************************/
/* Probability density function */
/*****************************************************************/

/************************************************/
/* Normal pdf */
/* Adapted from Scythe */
double mydnorm (double x, double mu, double sd, int l) {
  double X = (x - mu) / sd;
  if (l==1) {
    return -(M_LN_SQRT_2PI  +  0.5 * X * X + log(sd));
  }
  return (M_1_SQRT_2PI * exp(-0.5 * X * X) / sd);
}

/************************************************/
/* Bernoulli pdf */
double mydbern (int x, double p, int l) {
  if (p < 0 || p > 1) {
    fprintf(stderr, "p not in [0, 1]");
    exit(EXIT_FAILURE);
  }
  if (x != 0 && x != 1) {
    if (l == 1) {
      fprintf(stderr, "x => log(0)=nan in Bernoulli");
      exit(EXIT_FAILURE);
    }
    return 0.0;
  }
  if (l == 1) {
    if (p == 0 || p == 1) {
      fprintf(stderr, "p => log(0)=nan in Bernoulli");
      exit(EXIT_FAILURE);
    }
    return x * log(p) + (1-x) * log(1-p);
  }
  return pow(p,x) * pow(1-p,1-x); 
}

/************************************************/
/* Natural log of the Bernoulli pdf */
double mylndbern (int x, double p) {
    return x * log(p) + (1-x) * log(1-p);
}

/************************************************/
/* Binomial pdf */
/* Adapted from Scythe */

/* dbinom_raw */
static double dbinom_raw (double x, double n, double p, double q, int l) { 
  double lf, lc;
  if (p == 0)
    return((x == 0) ? 1.0 : 0.0);
  if (q == 0)
    return((x == n) ? 1.0 : 0.0);
  if (x == 0) { 
    if(n == 0)
      return 1.0;
        
    lc = (p < 0.1) ? -bd0(n, n * q) - n * p : n * log(q);
    return(exp(lc));
  }
  if (x == n) { 
    lc = (q < 0.1) ? -bd0(n,n * p) - n * q : n * log(p);
    return(exp(lc));
  }
  if (x < 0 || x > n)
    return 0.0;
  lc = stirlerr(n) - stirlerr(x) - stirlerr(n-x) - bd0(x,n*p) - bd0(n-x,n*q);
  lf = M_LN_2PI + log(x) + log1p(- x/n);
  // log 
  if (l == 1)
    return (lc - 0.5 * lf);
  return (exp(lc - 0.5 * lf));
}

/* mydbinom */
double mydbinom(double x, unsigned int n, double p, int l) {
  if (p < 0 || p > 1) {
    fprintf(stderr, "p not in [0, 1]");
    exit(EXIT_FAILURE);
  }
  double X = floor(x + 0.5);
  return dbinom_raw(X, n, p, 1 - p, l);
}
  
/*****************************************************************/
/* Random draws */
/*****************************************************************/

/*************/
/* myrunif() */
double myrunif(void) {
  return ((double)rand() + 0.5)/((double)RAND_MAX + 1.0);
}

/***************************/
/* myrgamma1(shape,rate=1) */
/* Function modified from the Scythe C++ library */
double myrgamma1 (double alpha) {

    double accept;
    int test;
    double u, v, w, x, y, z, b, c;
    
    // Implement Best's (1978) simulator
    b = alpha - 1;
    c = 3 * alpha - 0.75;
    test = 0;
    while (test == 0) {
	u = myrunif();
	v = myrunif();
	
	w = u * (1 - u);
	y = sqrt (c / w) * (u - .5);
	x = b + y;

	if (x > 0) {
            z = 64 * pow (v, 2) * pow (w, 3);
            if (z <= (1 - (2 * pow (y, 2) / x))) {
		test = 1;
		accept = x;
            } else if ((2 * (b * log (x / b) - y)) >= log (z)) {
		test = 1;
		accept = x;
            } else {
		test = 0;
            }
	}
    }
    
    return accept;
}

/**********************/
/* rnorm1, Knuth's 2nd volume of TAOCP 3rd edition page 122 */
double rnorm1 (void) {
  double v1,v2,s;

  do {
    v1 = 2.0 * ((double) rand()/RAND_MAX) - 1;
    v2 = 2.0 * ((double) rand()/RAND_MAX) - 1;

    s = v1*v1 + v2*v2;
  } while ( s >= 1.0 );

  if (s == 0.0)
    return 0.0;
  else
    return (v1*sqrt(-2.0 * log(s) / s));
}

/* myrnorm */
double myrnorm (double mean, double sd) {
    return (mean + rnorm1() * sd);
}

/**********************/
/* left truncated gamma */
/* Philippe, A. Simulation of right and left truncated gamma distributions by mixtures Statistics and Computing, 1997, 7, 173-181 */

/* the following function returns a random number from TG^+(a,b,1)            */
/* a=shape parameter, b=rate parameter                                        */
/* when a is an interger                                                      */
/* See Devroye, L. (1985)  Non-Uniform Random Variate Generation              */
/* Springer-Verlag, New-York.                                                 */
double integer(double a, double b)                             
{
        double u,x;
        double *wl,*wlc;
        int i;
        wl=(double *)malloc((int)(a+1)*sizeof(double));
        wlc=(double *)malloc((int)(a+1)*sizeof(double));
        wl[1]=1.0;
        wlc[1]=1.0;
        for(i=2; i<= (int)a ;i++ )
                {
                 wl[i]=wl[i-1]*(a-i+1)/b;
                 wlc[i]=wlc[i-1]+wl[i];
                 };
        for(i=1; i<= (int) a; i++)
                 {
                wlc[i]=wlc[i]/wlc[(int)a];
                 };
        u=myrunif();
        i=1;
        while(u>wlc[i]){i=i+1;};
        x=myrgamma1( (double) i)/b+1.0;        
        free(wl);
        free(wlc);               
        return(x);
}

/* the following function returns a random number from TG^+(a,b,1)            */  
/* a=shape parameter, b=rate parameter                                        */ 
double inter_le(double a, double b)
{
        double test=0,x,y,M;
        if (a<1.0)
            {
            M=1.0;
            while (test == 0)
                         {
                         x=1-(1/b)*log(1-myrunif());
                         y=1/pow(x,1-a);
                         if (myrunif()< y/M) test=1.0;
                         };
            }
            else
            {
            if (a<b) 
                      {
                       M=exp(floor(a)-a);
                       while (test == 0)
                            {
                            x=integer(floor(a), b*floor(a)/a);
                            y=pow(x, a-floor(a))*exp(-x*b*(1-floor(a)/a));
                            if (myrunif()< y/M) test=1.0;
                            };
                       }
                       else
                       {
                        M=exp(floor(a)-a)*pow(a/b,a-floor(a));
                        while (test == 0)
                           {
                            x=integer(floor(a), b+floor(a)-a);
                            y=pow(x, a-floor(a))*exp(-x*(-floor(a)+a));
                            if (myrunif()< y/M) test=1.0;
                            };
		       };
	   };
         return(x);
}

/* the following function returns a random number from TG^+(a,b,t)            */
/* a=shape parameter, b=rate parameter                                        */
double myrtgamma_left(double a, double b, double t)                                 
{
        return(inter_le(a, b*t)*t);
}


/*****************************************************************/
/* End of useful.c */
/*****************************************************************/
