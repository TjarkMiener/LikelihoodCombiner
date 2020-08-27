import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import os

from likelihood_combiner.reader import LklComReader
from likelihood_combiner.utils import *

def combiner(config, channel, sigmavULs=None, sigmavULs_Jnuisance=None, simulation_counter=None, simulations=[-1]):

    try:
        data_dir = config['Data']['data_directory']
        if data_dir is None:
            raise KeyError
    except KeyError:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/"))

    sources = config['Configuration']['sources']
    collaborations = config['Configuration']['collaborations']
    jnuisance = config['Data']['J_nuisance']

    # Initializing the LklComReader
    reader = LklComReader(channel, sources, collaborations)
    
    try:
        JFactor_file = config['Data']['JFactor_table']
        if JFactor_file is None:
            raise KeyError
    except KeyError:
        JFactor_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/Jfactor_Geringer-SamethTable.txt"))
            
    logJ, DlogJ = reader.read_JFactor(JFactor_file)
    # Reading in the the sigmav range and spacing. Round of the third digit to avoid an interpolation.
    sigmavMin = -(np.abs(np.floor(np.log10(np.abs(float(config['Data']['sigmaV_min'])))).astype(int))).astype(int)
    sigmavMax = -(np.abs(np.floor(np.log10(np.abs(float(config['Data']['sigmaV_max'])))).astype(int))).astype(int)
    sigmavNPoints = int(config['Data']['sigmaV_nPoints'])
    sigmav = np.logspace(sigmavMin, sigmavMax, sigmavNPoints, endpoint=True, dtype=np.float32)
    exponent = (np.abs(np.floor(np.log10(np.abs(sigmav))).astype(int))+3).astype(int)
    for i,e in enumerate(exponent):
        sigmav[i] = np.around(sigmav[i],decimals=e)

    for simulation in simulations:
        tstables = reader.read_tstables(data_dir, logJ, simulation)
        combined_ts = {}
        combined_ts_Jnuisance = {}
        mass_axis = []
        for source in sources:
            combined_source_ts = {}
            combined_source_ts_Jnuisance = {}

            # Check which collaboration observed the particular dSph
            for collaboration in collaborations:
                key = "{}_{}_{}".format(channel,source,collaboration)
                if key+'_ts' not in tstables:
                    # Delete invalid J-Factors and it's uncertainties
                    del logJ[source][collaboration]
                    del DlogJ[source][collaboration]

            # Compute the actual uncertainties, which is introduced in the combination.
            # Therefore we have to sort the DlogJ[source] in descending order and compute the
            # actual uncertainty using DlogJ_diff = (DlogJ[source]^2 - DlogJ_next[source]^2)^1/2.
            # For the last element DlogJ_diff is set to DlogJ[source]. After this computation,
            # DlogJ[source] holds a 2D array per collaboration with the uncertainty for a single
            # analysis and the uncertainty for the combined analysis.
            if jnuisance:
                DlogJ[source] = dict(sorted(DlogJ[source].items(), key=lambda x: x[1], reverse=True))
                prev_collaboration = None
                for collaboration in DlogJ[source]:
                    if prev_collaboration:
                        DlogJ_diff = 0.0
                        if DlogJ[source][prev_collaboration] != DlogJ[source][collaboration]:
                            DlogJ_diff = np.sqrt(np.power(DlogJ[source][prev_collaboration],2) - np.power(DlogJ[source][collaboration],2))
                        DlogJ[source][prev_collaboration] = [DlogJ[source][prev_collaboration], DlogJ_diff]
                    prev_collaboration = collaboration
                    prev_DlogJ = DlogJ[source][collaboration]
                DlogJ[source][prev_collaboration] = [prev_DlogJ, prev_DlogJ]

            # Combine ts values for the particular dSph
            for collaboration in DlogJ[source]:
                key = "{}_{}_{}".format(channel,source,collaboration)
                tstable = tstables[key+'_ts']
                masses = tstables[key+'_masses']
                sigmavFile = tstable[0]
                exponent = (np.abs(np.floor(np.log10(np.abs(sigmavFile))).astype(int))+3).astype(int)
                for i,e in enumerate(exponent):
                    sigmavFile[i] = np.around(sigmavFile[i],decimals=e)
                sigmavFile = sigmavFile[::-1]
                for i,m in enumerate(masses[1:]):
                    if m not in mass_axis:
                        mass_axis.append(m)
                    if source+"_"+str(m) not in combined_source_ts:
                        combined_source_ts[source+"_"+str(m)] = np.zeros(len(sigmav))
                        if jnuisance:
                            combined_source_ts_Jnuisance[source+"_"+str(m)] = np.zeros(len(sigmav))

                    ts_values = tstable[i+1][::-1]
                    if not np.all(ts_values == ts_values[0]):
                        if not np.array_equal(sigmav,sigmavFile):
                            lin_interpolation = interp1d(sigmavFile, ts_values, kind='linear', fill_value='extrapolate')
                            ts_values = lin_interpolation(sigmav)
                        combined_source_ts[source+"_"+str(m)] += ts_values
                        if jnuisance:
                            combined_source_ts_Jnuisance[source+"_"+str(m)] += ts_values
                            if DlogJ[source][collaboration][1] != 0.0:
                                combined_source_ts_Jnuisance[source+"_"+str(m)] = compute_Jnuisance(sigmav, combined_source_ts_Jnuisance[source+"_"+str(m)], DlogJ[source][collaboration][1])

            # Combine ts values for all dSphs
            for m in mass_axis:
                if str(m) not in combined_ts:
                    combined_ts[str(m)] = np.zeros(len(sigmav))
                    if jnuisance:
                        combined_ts_Jnuisance[str(m)] = np.zeros(len(sigmav))
                if source+"_"+str(m) in combined_source_ts:
                    if not np.all(combined_source_ts[source+"_"+str(m)] == combined_source_ts[source+"_"+str(m)][0]):
                        combined_ts[str(m)] += combined_source_ts[source+"_"+str(m)]
                        if jnuisance:
                            combined_ts_Jnuisance[str(m)] += combined_source_ts_Jnuisance[source+"_"+str(m)]

        # Compute the sigmav ULs per mass
        combined_sources_limits,combined_sources_sensitivity = compute_sensitivity(sigmav, combined_ts)
        if jnuisance:
            combined_sources_limits_Jnuisance,combined_sources_sensitivity_Jnuisance = compute_sensitivity(sigmav, combined_ts_Jnuisance)
                
        # Filling the data of the txt file into the table of the hdf5 file.
        sorted_mass = sorted(mass_axis)
        svUL = []
        svUL_Jnuisance = []
        for m in sorted_mass:
            svUL.append(combined_sources_limits[str(m)])
            if jnuisance:
                svUL_Jnuisance.append(combined_sources_limits_Jnuisance[str(m)])
            else:
                svUL_Jnuisance.append(np.nan)

        if sigmavULs is None and sigmavULs_Jnuisance is None:
            # Get the output directory
            try:
                output_dir = config['Output']['output_directory']
                if output_dir is None:
                    raise KeyError
            except KeyError:
                output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output/"))
            # Create output directory if it doesn't exist already
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            # Construct the h5 file
            try:
                h5file = config['Output']['hdf5_dataset']
                if h5file is None:
                    raise KeyError
            except KeyError:
                h5file = "lklcom"
            h5file = output_dir + h5file
            h5file = h5file.replace('.h5','')
            if simulation >= 0:
                h5file += "_{}_simu{}.h5".format(channel, simulation)
            else:
                h5file += "_{}_data.h5".format(channel)
            # Dumping the upper limits in the h5 file
            pd.DataFrame(data=sorted_mass).to_hdf(h5file, key='/masses', mode='w')
            pd.DataFrame(data=svUL).to_hdf(h5file, key='/sigmavULs', mode='a')
            if jnuisance:
                pd.DataFrame(data=svUL_Jnuisance).to_hdf(h5file, key='/sigmavULs_Jnuisance', mode='a')
            
        else:
            if simulation >= 0:
                h5_key = "{}_simu{}".format(channel, simulation)
            else:
                h5_key = "{}_data".format(channel)
                sigmavULs["{}_masses".format(channel)] = sorted_mass
                sigmavULs_Jnuisance["{}_masses".format(channel)] = sorted_mass

            sigmavULs[h5_key] = svUL
            sigmavULs_Jnuisance[h5_key] = svUL_Jnuisance

            if simulation >= 0:
                simulation_counter.value += 1
                progress_bar(simulation_counter.value,np.int(config['Data']['simulations']))

    del reader
    return

