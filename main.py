from util import *
from collections import Counter


def XR_KL(XR, XR_prjs):
    df = XR.loc[XR['READPRJ'].isin(XR_prjs[:])]  # select by project number
    df['READPRJ'] = pd.Categorical(df['READPRJ'], XR_prjs)
    df = df.sort_values(by=['ID', 'SIDE', 'READPRJ'])
    # drop duplication sorted by project number
    df_s = df.drop_duplicates(subset=['ID', 'SIDE'], keep='first')

    KL_R = df_s.loc[df_s['SIDE'] == 1, ['ID', 'V00XRKL']]
    KL_L = df_s.loc[df_s['SIDE'] == 2, ['ID', 'V00XRKL']]

    KL_R = KL_R.rename(columns={'V00XRKL': 'KL_R'})
    KL_L = KL_L.rename(columns={'V00XRKL': 'KL_L'})
    KL = pd.merge(KL_R, KL_L, on='ID', how='left')

    return KL


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
"""

dropbox = os.path.join(os.path.expanduser('~'), 'Dropbox')
DBPath = dropbox + '/MSK_shared/OAI_DataBase/'
Cli00, Enr, XR00, mri_moaks, dicom00 = oai_basic(DBPath)

""" Demographic baseline"""
# P02SEX: SEX
# P01BMI: BMI
# V00AGE: AGE
dem00 = pd.merge(Enr.loc[:, ['ID', 'P02SEX']], Cli00.loc[:, ['ID', 'P01BMI', 'V00AGE']], on='ID', how='left')

""" Basic clinical and enrollment variables"""
# P01KPNREV: Right Knee frequent pain
# P01KPNREV: Left Knee frequent pain
# V00WOMKPR: Right Knee WOMAC pain score
# V00WOMKPL: Left Knee WOMAC pain score
pain00 = Cli00.loc[:,['P01KPNREV', 'P01KPNLEV', 'V00WOMKPR', 'V00WOMKPL']]

""" KL grades from Semi-Quant X-Ray reading"""
KL00 = XR_KL(XR00, XR_prjs=['15', '37', '42'])

