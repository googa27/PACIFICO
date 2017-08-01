import openpyxl as pyxl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools as itr
import time
import os
import datetime
import xlsxwriter
import numbers
import sys

##################################### AUXILIARY FUNCTIONS #####################

#input: name of file
#output: date object of the file name
def to_date(filename):
    strings = filename.split('.')
    strings = strings[0].split('-')
    return datetime.date(int(strings[0][:4] ),
                         int(strings[1][:2] ),
                         int(strings[2][:2] ) )

def remove_unnamed(df):
    to_keep = [col for col in df.columns if type(col) != str or col.split(':')[0] != 'Unnamed']
    return df[to_keep]

################################################################################

## filter to take all data to one single excel file
def df_from_data(root = 'data', data_file = 'data.xlsx', selective_read = True):#implement read_all
    dfs = []
    if selective_read:
        data = pd.read_excel(data_file)
        data = data[data['path'] == data['path']]
        dfs.append(data)
        data_register =  data['path'].values
    columns = ['fecha', 'detalle', 'variedad_id', 'precio']
    for category in os.listdir(root):
        if category.split('-')[0] == 'Encuestador': # and category.split('-')[1] == 'Feria': #comentar condicion sobre feria
            print(category)
            for place in os.listdir(root + '/' + category):
                if not (place.endswith('.xlsm')):
                    print('--' + place)
                    for filename in os.listdir(root + '/' + category + '/' + place):
                        if filename.endswith('.xlsx') and filename[0].isnumeric():
                            file_path = category + '/' + place + '/' + filename
                            if not selective_read or not file_path in data_register:
                                print('----' + root + '/' + file_path)
                                print('------no esta en registro')
                                dataframes = pd.read_excel(root + '/' + file_path, None)
                                for df in dataframes.values():
                                    df = remove_unnamed(df)
                                    if len(df.columns) == 4:
                                        print('--------Valido')
                                        df.columns = columns
                                        df['fecha'] = to_date(filename)
                                        df['category'] = category
                                        df['place'] = place
                                        df['path'] = file_path
                                        dfs.append(df)
                                    elif category.split('-')[1] == 'Feria' and len(df.columns) == 6:
                                        print('--------ES FERIA!!!!!')
                                        precio = df.iloc[:, -3:].mean(axis = 1)
                                        df = df.iloc[:, :3]
                                        df['precio'] = precio
                                        df.columns = columns
                                        df['fecha'] =  to_date(filename)
                                        df['category'] = category
                                        df['place'] = place
                                        df['path'] = file_path
                                        dfs.append(df)
                                    else:
                                        df = pd.DataFrame({'path' : [file_path]})
                                        dfs.append(df)                                    
    return pd.concat(dfs)


####################################################################################################################################    

if __name__ == '__main__':
    start_time = time.time()

    data_file = 'data.xlsx'
    root = "C:\Dropbox (Team_Pacifico)\Pacifico\Chile\IPC\Bases\Encuestador"
    df_output = df_from_data(root = root, data_file = data_file, selective_read = True)

    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()

    destination = 'data.xlsx'
    writer = pd.ExcelWriter(destination)
    df_output.to_excel(writer, index = False)
    writer.save()
    
    print("--- %s seconds ---" % (time.time() - start_time))

#####################################################################################################################################
