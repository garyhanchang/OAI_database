from util import *
from collections import Counter
from functools import reduce
import numpy as np


def MOAKS_BML_vars(mri_moaks):
    """ Categories of MOAKS Variables """
    dropbox = os.path.join(os.path.expanduser('~'), 'Dropbox')
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


def XR_KL(df, XR_prjs, ver):
    df.columns = map(lambda x: str(x).upper(), df.columns)
    df = df.loc[df['READPRJ'].isin(XR_prjs[:])]  # select by project number

    df['READPRJ'] = pd.Categorical(df['READPRJ'], XR_prjs)
    df = df.sort_values(by=['ID', 'SIDE', 'READPRJ'])
    # drop duplication after sorted by project number
    df_s = df.drop_duplicates(subset=['ID', 'SIDE'], keep='first')
    KL = df_s.loc[:,['ID','SIDE','V' + ver + 'XRKL']]

    return KL

"""OAI basic data sheet of clinical, enrollment, x-ray and mri reading
DBPath: Path to the OAI database

Examples:
Cli00: Clinical baseline 
    ('AllClinical_SAS/AllClinical00.sas7bdat')
    
Enr: Enrollment 
    ('General_SAS/enrollees.sas7bdat')
    
XR00: Semi-Quant X-Ray reading baseline 
    ('X-Ray Image Assessments_SAS/Semi-Quant Scoring_SAS/kxr_sq_bu00.sas7bdat')
    
mri-moaks: MRI moaks score 
    ('MR Image Assessment_SAS/Semi-Quant Scoring_SAS/kmri_sq_moaks_bicl00.sas7bdat')
    
dicom00: path to the dicom files by imaging sequences of baseline dataset 
    (OAI_dicom_path_V00.xlsx')
    
Time points:
    00: baseline
    01: 12m 
    02: 18m (interim)
    03: 24m
    04: 30m (interim)
    05: 36m
    06: 48m
    07: 60m (phone)
    08: 72m 
    09: 84m (phone)
    10: 96m
    11: 108m (phone)
    99: outcomes

    
"""

dropbox = os.path.join(os.path.expanduser('~'), 'Dropbox')
DBPath = dropbox + '/MSK_shared/OAI_DataBase/'

OAI_path = {'CLI': 'AllClinical_SAS/AllClinical',
            'ENR': 'General_SAS/enrollees',
            'KXR_SQ': 'X-Ray Image Assessments_SAS/Semi-Quant Scoring_SAS/kxr_sq_bu',
            'MOAKS': 'MR Image Assessment_SAS/Semi-Quant Scoring_SAS/kmri_sq_moaks_bicl00'}

CLI00 = oai_path(DBPath, 'CLI', '00')
ENR = oai_path(DBPath, 'ENR', '')
moaks = oai_path(DBPath, 'MOAKS', '00')

""" Demographic baseline"""
# P02SEX: SEX
# P01BMI: BMI
# V00AGE: AGE
dem00 = pd.merge(ENR.loc[:, ['ID', 'P02SEX']], CLI00.loc[:, ['ID', 'P01BMI', 'V00AGE']], on='ID', how='left')

""" Basic clinical and enrollment variables"""
# P01KPNREV: Right Knee frequent pain
# P01KPNREV: Left Knee frequent pain
# V00WOMKPR: Right Knee WOMAC pain score
# V00WOMKPL: Left Knee WOMAC pain score
pain00 = CLI00.loc[:, ['P01KPNREV', 'P01KPNLEV', 'V00WOMKPR', 'V00WOMKPL']]


""" KL grades from Semi-Quant X-Ray reading at different time points"""
XR = {}
KL = {}
ver_list = ['00', '01', '03', '05']  # baseline, 12m, 24m, 36m
for ver in ver_list:
    XR[ver] = oai_path(DBPath, 'KXR_SQ', ver)
    KL[ver] = XR_KL(XR[ver], XR_prjs=[b'15', b'37', b'42'], ver=ver)

to_merge = [KL[v] for v in ver_list]
KL = reduce(lambda left, right: pd.merge(left, right, on=['ID', 'SIDE'], how='left'), to_merge)

compare_time_pts = [[2, 3], [2, 4], [2, 5]]  # compare 12m, 24m, 36m to baseline

df = pd.concat([KL.loc[(KL[KL.columns[x][0]] < 2) & (KL[KL.columns[x][1]] >= 2), :]
                for x in compare_time_pts]).drop_duplicates().reset_index(drop=True)
print('KL<2 at baseline, >=2 at 12m, 24m or 36m. Find: ' + str(len(df)) + ' knees')
df.to_csv('KL_a.csv')

df = pd.concat([KL.loc[(KL[KL.columns[x][1]] - KL[KL.columns[x][0]] >= 2), :]
                for x in compare_time_pts]).drop_duplicates().reset_index(drop=True)
print('KL progress >=2 compared to baseline. Find: ' + str(len(df)) + ' knees')
df.to_csv('KL_b.csv')

