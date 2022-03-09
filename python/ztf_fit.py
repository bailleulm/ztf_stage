from ztf_hdf5 import Write_LightCurve, Read_LightCurve, Plot_LightCurve
import sncosmo
from astropy.table import QTable, Table, Column, vstack, MaskedColumn
import numpy as np

class SN_fit:
    "Definition of a class fit lightcurve"
    
    def __init__(self, lc, param = ['z', 't0', 'x0', 'x1', 'c'] ,list_param = ['z', 'z_err', 't0', 't0_err', 'x0', 'x0_err', 
                                                                             'x1', 'x1_err', 'c', 'c_err','chisq', 'ndof',
                                                                             'z_t0_cov', 'z_x0_cov','z_x1_cov',
                                                                             'z_c_cov','x0_t0_cov','x0_x1_cov',
                                                                             'x0_c_cov', 't0_x1_cov', 't0_c_cov', 'x1_c_cov'],
                 z_bound_err = 0.0001):
        """
        Parameters
        ----------
        lc : AstropyTable
            AstropyTable of your selecting light curve.
        z_bounds : dict
            redshift range for the fit (default = {'z':(0.01, 0.1)}).
        """
        dustmap = sncosmo.OD94Dust()
        self.lc = lc
        self.source = sncosmo.get_source('salt2-extended', version='1.0')
        self.model = sncosmo.Model(source=self.source, effects=[dustmap, dustmap],
                                                       effect_names=['host', 'mw'],
                                                       effect_frames=['rest', 'obs'])
        self.model.set(mwebv=lc.meta['mwebv'])
        self.param = param
        self.z_bounds = {'z':(lc.meta['z']-z_bound_err, lc.meta['z']+z_bound_err)}
        self.list_param = list_param
        if not 'z' in self.param:
            self.model.set(z=lc.meta['z'])
    
    def fit_sn(self):
        """
        Return
        ------
        result, fitted_model : class sncosmo
            result of the fit with sncosmo.
        """
        try:
            result, fitted_model = sncosmo.fit_lc(self.lc, self.model, self.param, bounds=self.z_bounds)
            return result, fitted_model
            
        except:
            print("WARNING : That was no valid light curve.")
    
    def flatten(self):
        result, fitted_model = self.fit_sn()
        return sncosmo.flatten_result(result)
    
    def add(self):
        t = []
        fl = self.flatten()
        t.append(fl)
        t = Table(t)
        return t[self.list_param]
    
    def plot_sn(self):
        result, fitted_model = self.fit_sn()
        try:
            return sncosmo.plot_lc(self.lc, model=fitted_model, errors=result.errors)
        except:
            print("No plot for this light curve")
    
    def info(self):
        result, fitted_model = self.fit_sn()
        print("Number of chi^2 function calls:", result.ncall)
        print("Number of degrees of freedom in fit:", result.ndof)
        print("chi^2 value at minimum:", result.chisq)
        print("model parameters:", result.param_names)
        print("best-fit values:", result.parameters)
        print("The result contains the following attributes:\n", result.keys())
        print("Errors corresponding to the different fitting parameters:\n", result.errors)
        print('result.success: \n', result.success)
        print('result.message: \n', result.message)
        print('result.vparam_names: \n', result.vparam_names)
        print('Matrice de covariance : \n', result.covariance)
        print('result.nfit: \n', result.nfit)
        print('result.data_mask: \n', result.data_mask)
        

class SN_fit_tab:
    "Definition of a class which add different result from sncosmo.fit_lc to your meta data file"
    
    def __init__(self, metaTable, dataFile, param = ['z', 't0', 'x0', 'x1', 'c']):
        """
        Parameters
        ----------
        metaTable : AstropyTable
            AstropyTable of the meta data of your selected light curve (pass selec == 1).
        """
        
        self.param = param
        self.metaTable = metaTable
        self.dataFile = dataFile
        self.keys = []
        self.list1 = ['z', 't0', 'x0', 'x1', 'c']
        self.list2 = ['z_fit', 't0_fit', 'x0_fit', 'x1_fit', 'c_fit']
    
    def table_param(self):
        """
        Return
        ------
        t : Table
            Table with the different parameters on list_param that you generate with sncosmo.fit_lc.
        """
        t = []
        for i, row in enumerate(self.metaTable):
            path = row['path']
            self.keys.append(path)
            data = Read_LightCurve(file_name=self.dataFile)
            lc = data.Read_file(path=path)
        
            fit = SN_fit(lc, param=self.param)
            try:
                result, fitted_model = fit.fit_sn()
                fl = fit.add()
                t = vstack([t, fl])
            except:
                print('None')
                a = np.full(len(fit.list_param), -1)
                a = Table(a, names = fit.list_param)
                t = vstack([t, a])
        t.add_column(self.keys, name='path', index=0)
        for i, name in enumerate(self.list1):
            t.rename_column(name, self.list2[i])
        
        return t
    
    def addto_meta(self):
        """
        Return
        ------
        new_meta : AstropyTable
            AstropyTable with starting meta data and fitted meta data (and the different parameters on list_param).
        """
        
        fit_param = self.table_param()
        new_meta = self.metaTable
        for i, col in enumerate(fit_param.columns):
            if col == 'path':
                new_meta[col] = fit_param[col]
            else:
                c = MaskedColumn(fit_param[col])
                new_meta.add_column(c)
        return new_meta
