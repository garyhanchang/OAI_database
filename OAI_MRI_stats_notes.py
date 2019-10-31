""" importing basic functions"""
import pandas as pd
import numpy as np
import os
from collections import Counter

""" basic parameters for pandas display"""
#pd.set_option('display.max_row', 1000)
#pd.set_option('display.max_columns', 5)


""" OAI ID and Pain Label """
DBPath = '/Users/ghc/Dropbox/0_KeeProj/Proj_Knee_Stat/DataBase/'


""""""
clinical_path = os.path.join(DBPath, 'AllClinical_SAS/AllClinical00.sas7bdat') #combine database path + certian file
Cli00 = pd.read_sas(clinical_path)  # load the database using the combined path

print(type(Cli00))  # type of database
print(Cli00.shape)  # 4796 subjects, 1187 variables

print(Cli00.head())
print(Cli00.tail())

""" basic numpy slicing """
vars = Cli00.columns.values # save name of columns into a numpy array
print(vars[0])  #first var
print(vars[:10])  # first 10
print(vars[10:])  # last 10
print(vars[2:6])  # slice from 2 to 5 (6-1!!!)

""" basic pandas operation"""
print(Cli00['ID'].unique())  # print unique patient id
print(Cli00['ID'].unique().shape)  # number of unique patient id

Enr = pd.read_sas(os.path.join(DBPath, 'General_SAS/enrollees.sas7bdat'))
XR00 = pd.read_sas(os.path.join(DBPath, 'X-Ray Image Assessments_SAS/Semi-Quant Scoring_SAS', 'kxr_sq_bu00.sas7bdat'))

""" MRI reading data """
mri_moaks = pd.read_sas(DBPath + 'MR Image Assessment_SAS/Semi-Quant Scoring_SAS/kmri_sq_moaks_bicl00.sas7bdat')
mri_moaks['ID'] = (mri_moaks['ID'].str.decode("utf-8"))
mri_moaks['READPRJ'] = (mri_moaks['READPRJ'].str.decode("utf-8"))


""" basic pandas operation"""
print(mri_moaks.loc[mri_moaks['READPRJ']=='65', ['ID','READPRJ']]) # selecting only READPRJ 65
print(mri_moaks.loc[(mri_moaks['READPRJ'].isin(['65', '22', '63F', '63A'])), ['ID','READPRJ']]) # from PRJ 65 22 63F 63A
print(mri_moaks.loc[mri_moaks['V00MBMSFMC'] >= 2,'ID'].unique())  #unique subjects with femur lateral central BML >=2
print(mri_moaks.loc[(mri_moaks['READPRJ'] == '65') & (mri_moaks['V00MBMSFMC'] >= 2),['ID','READPRJ','V00MBMSFMC']]) # in PRJ 65 and BML >=2 .....

""" Categories of MOAKS Variables """
moaks_excel = pd.read_excel('KMRI_SQ_MOAKS_stats.xlsx')
moaks_vars = dict()
for ii in moaks_excel['KIND'].unique():
    moaks_vars[ii] = list(moaks_excel.loc[moaks_excel['KIND'] == ii]['NAME'].values)

""" Description for MOAKS """
moaks_prjs = ['65', '22', '30', '63E', '63A', '63F', '63C', '63B', '63D']

df = mri_moaks.loc[mri_moaks['READPRJ'].isin(moaks_prjs[:1])]  # select by project number
print(df.groupby(['ID', 'SIDE']).size().reset_index(name='Freq').shape)

df2 = df[moaks_vars['BML Size']].copy()
for v in moaks_vars['BML Size']:
    df2[v] = (df2[v] >= 2).astype(int)

print(Counter(df2.sum(axis=1)))

