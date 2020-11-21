// ==============================================================================
// author          :Ghislain Vieilledent
// email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
// web             :https://ecology.ghislainv.fr
// python_version  :2.7
// license         :GPLv3
// ==============================================================================

// Prototype of useful functions
double logit (double x);
double invlogit (double x);
double mydnorm (double x, double mu, double sd, int l);
double mydbern (int x, double p, int l);
double mylndbern (int x, double p);
double mydbinom (double x, unsigned int n, double p, int l);
double myrunif(void);
double myrgamma1(double alpha);
double rnorm1(void);
double myrnorm(double mean, double sd);
double integer(double a, double b);
double inter_le(double a, double b);
double myrtgamma_left(double a, double b, double t);

// EOF
