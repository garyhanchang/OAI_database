from collections import Counter
from functools import reduce
import os
import pandas as pd
import numpy as np


def oai_path(DBPath, key, ver):

    """Return a dataframe given a specific category of OAI data and the version number
    Args:
        DBPath: Path to the root of OAI database

        key: category of OAI files
            CLI: Clinical
                ex: 'AllClinical_SAS/AllClinical00.sas7bdat' for clinical baseline

            ENR: Enrollment
                ex: 'General_SAS/enrollees.sas7bdat', there is no version number

            KXR_SQ: Semi-Quant X-Ray reading
                ex: X-Ray Image Assessments_SAS/Semi-Quant Scoring_SAS/kxr_sq_bu00.sas7bdat' for baseline

            MOAKS: MRI moaks score
                ex: 'MR Image Assessment_SAS/Semi-Quant Scoring_SAS/kmri_sq_moaks_bicl00.sas7bdat' for baseline

            dicom00: path to the dicom files by imaging sequences of baseline dataset (not included in original file)
                ex: (OAI_dicom_path_V00.xlsx')

        ver: version number of time points:
            00: baseline
            01: 12m
            02: 18m (interim, no images)
            03: 24m
            04: 30m (interim, no images)
            05: 36m
            06: 48m
            07: 60m (phone, no images)
            08: 72m
            09: 84m (phone, no images)
            10: 96m
            11: 108m (phone, no images)
            99: outcomes
            
    Returns:
        x: pandas dataframe

    """

    path_dict = {'CLI': 'AllClinical_SAS/AllClinical',
                 'ENR': 'General_SAS/enrollees',
                 'KXR_SQ': 'X-Ray Image Assessments_SAS/Semi-Quant Scoring_SAS/kxr_sq_bu',
                 'MOAKS': 'MR Image Assessment_SAS/Semi-Quant Scoring_SAS/kmri_sq_moaks_bicl'}

    x = pd.read_sas(os.path.join(DBPath, path_dict[key] + ver + '.sas7bdat'))
    x['ID'] = (x['ID'].str.decode("utf-8"))  # ID as string

    return x


def oai_basic():
    CLI00 = oai_path(DBPath, 'CLI', '00')
    ENR = oai_path(DBPath, 'ENR', '')
    moaks = oai_path(DBPath, 'MOAKS', '00')

    """ Demographic baseline"""
    # P02SEX: SEX
    # P01BMI: BMI
    # V00AGE: AGE
    dem00 = pd.merge(ENR.loc[:, ['ID', 'P02SEX']], CLI00.loc[:, ['ID', 'P01BMI', 'V00AGE']], on='ID', how='left')

    """ Basic clinical and enrollment variables"""
    # P01KPNREV: Right Knee frequent pain (0 or 1, no follow up)
    # P01KPNREV: Left Knee frequent pain
    # V00WOMKPR: Right Knee WOMAC pain score  (0-20, have follow ups)
    # V00WOMKPL: Left Knee WOMAC pain score
    pain00 = CLI00.loc[:, ['P01KPNREV', 'P01KPNLEV', 'V00WOMKPR', 'V00WOMKPL']]

    return dem00, pain00


def MOAKS_BML_vars(mri_moaks):
    """ Return a dataframe of subjects with BML larger than 1 in any location

    """
    moaks_excel = pd.read_excel(dropbox + '/MSK_shared/OAI_DataBase/MOAKS/KMRI_SQ_MOAKS_stats.xlsx')
    moaks_vars = dict()
    for ii in moaks_excel['KIND'].unique():
        moaks_vars[ii] = list(moaks_excel.loc[moaks_excel['KIND'] == ii]['NAME'].values)

    """ Description for MOAKS """
    moaks_prjs = ['65', '22', '30', '63A', '63B', '63C', '63D', '63E', '63F']  # all the moaks prjs
    df = mri_moaks.loc[mri_moaks['READPRJ'].isin(moaks_prjs[:1])]  # select by project number
    df['READPRJ'] = pd.Categorical(df['READPRJ'], moaks_prjs)
    df = df.sort_values(by=['ID', 'SIDE', 'READPRJ'])
    df_s = df.drop_duplicates(subset=['ID', 'SIDE'], keep='first')

    df2 = df_s[['ID', 'SIDE', 'READPRJ'] + moaks_vars['BML Size']].copy()

    for v in moaks_vars['BML Size']:  # threshold by BML size
        df2[v] = (df2[v] >= 1).astype(int)

    print(Counter(df2[moaks_vars['BML Size']].sum(axis=1)))
    return df2


class read_XR:
    def __init__(self, var_list, prjs, ver_list):
        """ Read Semi-Quant X-Ray reading from differnt versions ang merge them by subject ID and side of the knee

        Attributes:
            var_list (list of str): list of variables to be extracted
            prjs (list of str): list of reading projects.
                The output dataframe will be merged according to the order of the list
            ver_list (list of str): list of versions to be merged
        """
        data = {}
        for ver in ver_list:
            y = oai_path(DBPath, 'KXR_SQ', ver)
            """ Reading KL grades from Semi-Quant X-Ray reading """
            y.columns = map(lambda x: str(x).upper(), y.columns)
            y = y.loc[y['READPRJ'].isin(prjs[:])]  # select by project number

            y['READPRJ'] = pd.Categorical(y['READPRJ'], prjs)
            y = y.sort_values(by=['ID', 'SIDE', 'READPRJ'])
            # drop duplication after sorted by project number
            y = y.drop_duplicates(subset=['ID', 'SIDE'], keep='first')

            var_name = [x.replace('$$', ver) for x in var_list]
            y = y.loc[:, ['ID', 'SIDE'] + var_name]

            data[ver] = y.where(pd.notnull(y), None)  # this is still wrong, there are nan and None

        to_merge = [data[v] for v in ver_list]
        self.data = reduce(lambda left, right: pd.merge(left, right, on=['ID', 'SIDE'], how='left'), to_merge)

        self.print_summary()

    def print_summary(self):
        """ print summary of the dataframe """
        print(self.data.head())
        print(self.data.tail())
        print('Columns:')
        print(self.data.columns.values)

    def compare_pairs(self, var, ver0, ver1, mode, criteria):
        """Compare a variable longitudinally
        Args:
            var (str): name of the variable to compare to
            ver0 (str): version name of the base period
            ver1 (list of str): list of version names of the follow-up time points
            mode (str): absolute for individual criteria, difference for differential criteria
            criteria (float): value of the criteria
        """

        XR = self.data
        var0 = var.replace('$$', ver0)
        var1 = [var.replace('$$', x) for x in ver1]
        if mode == 'difference':
            selected = pd.concat([XR.loc[(XR[y] - XR[var0] >= criteria), :]
                                  for y in var1]).drop_duplicates().reset_index(drop=True)
        if mode == 'absolute':
            selected = pd.concat([XR.loc[(XR[var0] < criteria[0]) & (XR[y] >= criteria[1]), :]
                                  for y in var1]).drop_duplicates().reset_index(drop=True)

        return selected.loc[:, ['ID', 'SIDE']+[var.replace('$$', y) for y in [ver0] + ver1]]


def main():
    """ change the path to you database folder """
    global dropbox
    global DBPath
    dropbox = os.path.join(os.path.expanduser('~'), 'Dropbox')
    DBPath = dropbox + '/MSK_shared/OAI_DataBase/'

    """ Read from Semi-Quant X-Ray reading at different time points
    XRKL: KL grade, XRJSM: Joint space median, XRJSL: Joint space lateral"""

    var_list = ['V$$XRKL', 'V$$XRJSM', 'V$$XRJSL']
    prjs = [b'15', b'37', b'42'][:1] # just use project 15 for now
    ver_list = ['00', '01', '03', '05']
    XR = read_XR(var_list=var_list, prjs=prjs, ver_list=ver_list)

    """Some examples of longitudinal comparison"""
    s = XR.compare_pairs(var='V$$XRKL', ver0='00', ver1=['01', '03', '05'], mode='absolute', criteria=[2, 2])
    print('KL<2 at baseline, >=2 at 12m, 24m or 36m. Find: ' + str(len(s)) + ' knees')  # should be 398

    s = XR.compare_pairs(var='V$$XRKL', ver0='00', ver1=['01', '03', '05'], mode='difference', criteria=2)
    print('KL progress >=2 compared to baseline. Find: ' + str(len(s)) + ' knees')  # should be 210

    s = XR.compare_pairs(var='V$$XRJSM', ver0='00', ver1=['01', '03', '05'], mode='difference', criteria=1)
    print('Joint space narrowing (medial) progress >=2 compared to baseline. Find: ' + str(len(s)) + ' knees')  # should be 558

    s = XR.compare_pairs(var='V$$XRJSL', ver0='00', ver1=['01', '03', '05'], mode='difference', criteria=1)
    print('Joint space narrowing (lateral) progress >=2 compared to baseline. Find: ' + str(len(s)) + ' knees')  # should be 246


if __name__ == "__main__":
    main()

