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
import numbers

##################################### AUXILIARY FUNCTIONS #####################

#input: name of file
#output: date object of the file name
def to_date_jumbo(filename):
    filedate = filename.split()[1]
    strings = filedate.split('.')
    strings = strings[0].split('-')
    return datetime.date(int(strings[0][:4] ),
                         int(strings[1][:2] ),
                         int(strings[2][:2] ) )

def remove_unnamed(df):
    to_keep = [col for col in df.columns if type(col) != str or col.split(':')[0] != 'Unnamed']
    return df[to_keep]

################################################################################

## filter to take all data to one single excel file
def df_from_data_jumbo(root = "C:\Dropbox (Team_Pacifico)\Pacifico\Chile\IPC\Items\Alimentos\Carro-Online",
                       data_file = 'data_jumbo.xlsx', selective_read = True):
    dfs = []
    data_register = []
    if selective_read and os.path.isfile(root + "\data_jumbo"):
        data = pd.read_excel(data_file)
        data = data[data['path'] == data['path']]
        dfs.append(data)
        data_register =  data['path'].values
    columns = ['codigo', 'producto', 'cantidad', 'precio_unitario', 'unidad']
    for filename in os.listdir(root + "\Jumbo"):
        file_path = root + '/Jumbo/' + filename
        if (filename.endswith('.xlsx') or filename.endswith(".xls")) and filename[0]== "J":
            print(filename[0])
            if not selective_read or not file_path in data_register:
                print('----' + file_path)
                print('------no esta en registro')
                dataframes = pd.read_excel(file_path, None)
                for df in dataframes.values():
                    df = remove_unnamed(df)
                    if len(df.columns) == 5:
                        print('--------Valido')
                        df.columns = columns
                        df['fecha'] = to_date_jumbo(filename)
                        df['categoria_jumbo'] = df.codigo.apply(lambda x : x if x.isalpha() else np.nan )
                        df['categoria_jumbo'] = df.categoria_jumbo.fillna(method = 'ffill')
                        df = df.dropna(axis = 0, how = 'any')
                        df['path'] = file_path
                        dfs.append(df)
                    else:
                        df = pd.DataFrame({'path' : [file_path]})
                        dfs.append(df)                                    
    return pd.concat(dfs)


####################################################################################################################################    

if __name__ == '__main__':
    start_time = time.time()

    data_file = 'data_jumbo.xlsx'
    root = "C:\Dropbox (Team_Pacifico)\Pacifico\Chile\IPC\Items\Alimentos\Carro-Online"
    df_output = df_from_data_jumbo(root = root, data_file = data_file, selective_read = True)

    print("--- %s seconds ---" % (time.time() - start_time))

    start_time = time.time()

    destination = 'data_jumbo.xlsx'
    writer = pd.ExcelWriter(destination)
    df_output.to_excel(writer, index = False)
    writer.save()
    
    print("--- %s seconds ---" % (time.time() - start_time))

################################################################################

    df = pd.read_excel("C:\Dropbox (Team_Pacifico)\Pacifico\Chile\IPC\Items\Alimentos\Carro-Online\Jumbo\Jumbo 2017-05-26.xls")
    df.columns = ['codigo', 'producto', 'cantidad', 'precio_unitario', 'unidad']
    df["categoria_jumbo"] = df.codigo.apply(lambda x : x if x.isalpha() else np.nan )
    df["categoria_jumbo"] = df.categoria_jumbo.fillna(method = "ffill")
    df = df.dropna(axis = 0, how = "any")
    print(df.head())
