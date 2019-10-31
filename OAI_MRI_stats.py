from collections import Counter
from util import *


def XR_KL00():
    XR_prjs = ['15', '37', '42']  # all the moaks prjs
    df = XR00.loc[XR00['READPRJ'].isin(XR_prjs[:])] # select by project number
    df['READPRJ'] = pd.Categorical(df['READPRJ'], XR_prjs)
    df = df.sort_values(by=['ID', 'SIDE', 'READPRJ'])
    df_s = df.drop_duplicates(subset=['ID', 'SIDE'], keep='first')

    KL_R = df_s.loc[df_s['SIDE'] == 1, 'V00XRKL']
    KL_L = df_s.loc[df_s['SIDE'] == 2, 'V00XRKL']

    return KL_L, KL_R


def MOAKS_BML_vars():
    """ Categories of MOAKS Variables """
    dropbox = os.path.join(os.path.expanduser('~'), 'Dropbox')
    moaks_excel = pd.read_excel(dropbox + '/MSK_shared/OAI_Labels/MOAKS/KMRI_SQ_MOAKS_stats.xlsx')
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


""" OAI basic data """
Cli00, Enr, XR00, mri_moaks, mri00 = oai_basic()

df2 = MOAKS_BML_vars()
df2 = df2.reset_index()


## KMRI_SQ_MOAKS ()