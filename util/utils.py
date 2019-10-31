""" importing basic functions"""
import pandas as pd
import os
from distutils.dir_util import copy_tree
import os


def oai_basic(DBPath):
    """OAI basic data sheet of clinical, enrollment, x-ray and mri reading
    Cli00: Clinical baseline
    Enr: Enrollment
    XR00: Semi-Quant X-Ray reading baseline
    mri-moaks: MRI moaks score
    dicom00: path to the dicom files by imaging sequences of baseline dataset
    """

    clinical_path = os.path.join(DBPath, 'AllClinical_SAS/AllClinical00.sas7bdat')
    Cli00 = pd.read_sas(clinical_path)
    Cli00['ID'] = (Cli00['ID'].str.decode("utf-8"))  # ID as string

    Enr = pd.read_sas(os.path.join(DBPath, 'General_SAS/enrollees.sas7bdat'))
    Enr['ID'] = (Enr['ID'].str.decode("utf-8"))  # ID as string

    """ XR reading data """
    XR00 = pd.read_sas(os.path.join(DBPath, 'X-Ray Image Assessments_SAS/Semi-Quant Scoring_SAS', 'kxr_sq_bu00.sas7bdat'))
    XR00['ID'] = (XR00['ID'].str.decode("utf-8"))  # ID as string
    XR00['READPRJ'] = (XR00['READPRJ'].str.decode("utf-8"))  # Read Project as string

    """ MRI reading data """
    mri_moaks = pd.read_sas(DBPath + 'MR Image Assessment_SAS/Semi-Quant Scoring_SAS/kmri_sq_moaks_bicl00.sas7bdat')
    mri_moaks = mri_moaks.drop_duplicates()  # moaks has duplicated entries
    mri_moaks['ID'] = (mri_moaks['ID'].str.decode("utf-8"))
    mri_moaks['READPRJ'] = (mri_moaks['READPRJ'].str.decode("utf-8"))

    """ OAI_MRI_v00_location"""
    dicom00 = pd.read_excel(DBPath + '/OAI_dicom_path_V00.xlsx')
    dicom00['ID'] = dicom00['ID'].values.astype('str')

    return Cli00, Enr, XR00, mri_moaks, dicom00


def copy_selected_data(df2, mri00, out_path='BML_test/', in_path='media/ghchang/GUERMAZI_BL/'):

    series_left = mri00.columns.values[8:13]
    series_right = mri00.columns.values[list(range(15, 19)) + [20]]

    for ii in range(172):
        ID = df2['ID'].values[ii]
        side = df2['SIDE'].values[ii]
        try:
            os.mkdir(out_path + ID)
        except:
            pass

        if side == 1:
            series = series_right
        if side == 2:
            series = series_left

        for x in series:
            ori_path = mri00.loc[mri00['ID'] == ID][x].values[0]
            copy_tree(ori_path, out_path + ID + '/' + x)

