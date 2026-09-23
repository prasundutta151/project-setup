this project usees astropy to do optioations in image
the implementation will be with cli options, with argperser as a separate function

this code does chi sq fitting to data to arbitrary functions with or without binning the data and with or without errors in y axis ( if not there assumed all 1)

take a multi column csv file with different columns having different data, with the header line explaining them and the second header giving the units

user can give input to the x-col, y-col and err-col if not given first three are chosen for these, if x and y are given std in y is taken as err for all y

user can give limits in x, plot limits in x (they can be separate), both lower and upper limit using same cli

user can choose plot-only option to see the plots initially

user can choose axis-type as all combination of log, lin and exp like log-exp etc

user can choose with-bin binning options can be uniform/std/mad where uniform use same no of data points to bin, std keep std same in each bin to 10% and mad keepd mad same in each bin to 10% this 10% can be changed with with-bin-per (optional argument default 10)

user can choose plot with plot file name

use can choose --fit custom_fits_file name

the custom file will have the following format
it is a .py file
first it will have choice for the function to fit, where fitfunction="function mane" where function ame function will be available in same file
then fit range can be chosen same syntex as limits in x and y for plotting
the user can give parameters and their ranges and initial values like for parameter A, A:<inti val>:T:(low, high)
, where T is that this parameter to be used to fit, else if F is given initial value will be used only, parameter not fit
if any entry after A is not to be given a - can be used there

fit_parameter_filename with path will be given in this also

below will be diff fit functions, there can be many and the fitfunction choice above decides which one
