def sing_exp(x, tau, b):
    return contrast*np.exp(-2*((x/tau)))+b

g2_fit = np.zeros([cv_dim,2])
g2_fit_err = np.zeros([cv_dim,2])


for ii in range(cv_dim):

    p0_guess = [1e-4,1]
    b_min = [1e-6,0.99]
    b_max = [1e-2,1.03]

    popt, pcov = curve_fit(sing_exp, t_el, g2_ave[:,ii], p0 = p0_guess, sigma=g2_ave_err[:,ii],
                           bounds=(b_min, b_max))

    g2_fit[ii,:] = popt
    g2_fit_err[ii,:] = np.sqrt(np.diag(pcov))

xfine = np.logspace(-5, 0.5, num=40)
