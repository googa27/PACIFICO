import openpyxl as pyxl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools as itr
import time
import os
import datetime
import xlsxwriter
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.neural_network import MLPClassifier
import time
import numbers
#import editdistance as ed
import sys

from bokeh.plotting import figure
from bokeh.io import output_file, show, curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource, Slider, Select 


############################################# FUNCTIONS FOR HANDLING DATA ####################################################

#input: name of file
#output: date object of the file name
def date(filename):
    if type(filename) == datetime.date:
        return filename
    if filename != filename:
        return datrime.date(1914, 1, 1)#default date
    if type(filename) != str:
        print(filename)
    strings = filename.split('.')
    strings = strings[0].split('-')
    if len(strings) == 3:
        return datetime.date(int(strings[0]),
                             int(strings[1]),
                             int(strings[2]))
    if len(strings) == 2:
        return datetime.date(int(strings[0]),
                             int(strings[1]),
                             1)

def is_valid_difference(years, months):
    if years == 1:
        if months == -11:
            return True
    if years == 0:
        if months == 1:
            return True
    return False

##returns true if x.month is the month before y.month, false otherwise
def date_is_precedent(x, y):
    if x != x or y !=y: #to detect NANs
        return False
    x_date, y_date = date(x), date(y)
    decision_month = y_date.month - x_date.month
    decision_year = y_date.year - x_date.year
    return is_valid_difference(decision_year, decision_month)


#############################################FUNCTIONS FOR SAVING AND LOADING DATA##########################################


def save_pickles(product_list = 'data.xlsx', id_list = 'producto_id.xlsx'):
    if not(product_list.endswith('.xlsx') and id_list.endswith('.xlsx')):
        print('ERROR: One or more of the given files are not excel files (.xlsx)')
        return
    data_df = pd.read_excel(product_list)
    producto_id = pd.read_excel(id_list, index_col = 0)
    data_df.to_pickle(product_list.split('.')[0] + '.pkl')
    producto_id.to_pickle(id_list.split('.')[0] + '.pkl')

def load_pickles(product_list = 'data.pkl', id_list = 'producto_id.pkl'):
    return pd.read_pickle(product_list), pd.read_pickle(id_list)

################################################################################################################################

def get_upper(s):
    return ''.join([c for c in s if not c.islower()])

def score_coincidence(detalle, s):
    ld = [word for word in detalle.split(' ') if word.isupper()]
    ls = [word for word in s.split(' ') if word.isupper()]
    complete_word_score = [len(word) in ld for word in ls if len(word)>4]
    incomplete_word_score = [len(word)*any(word in biggerword for biggerword in ld) for word in ls if len(word)>4]
    return sum(complete_word_score)*10000 + sum(incomplete_word_score)

def best_coincidence(detalle, producto_id):
    return min(producto_id.index.to_series(), key = lambda x: ed.eval(get_upper(detalle), x) )
        

def infer_product_id(df, producto_id):
    df_producto = df.detalle.apply(lambda x: best_coincidence(x, producto_id)[1])
    for i in df_out.index:
        if i%100 == 0:
            print(i)
        row = df_out.loc[i]
        if row['producto'] !=  row['producto'] and row['producto_id'] !=  row['producto_id'] and row['detalle'] == row['detalle']: #to detect nans
            score, best_producto, best_producto_id = best_coincidence(row['detalle'], producto_id)
            if score>0:
                df_out.loc[i, 'producto'], df_out.loc[i, 'producto_id'] = best_producto, best_producto_id
    return df_out


def eliminate_nodetail_or_noprice(df):
    bool_nonull = df['variedad_id'].apply(lambda x: x != 0)
    bool_precio = df['precio'] == df['precio']
    bool_detalle = df['detalle'] == df['detalle']
    bool_varid = df['variedad_id'] == df['variedad_id']
    bool_type_precio = df['precio'].apply(lambda x : isinstance(x, numbers.Number))
    bool_type_varid = df['variedad_id'].apply(lambda x : isinstance(x, numbers.Number))
    bool_type_detalle = df['detalle'].apply(lambda x : isinstance(x, str))
    return df[bool_precio & bool_detalle & bool_varid & bool_nonull
              & bool_type_precio & bool_type_detalle & bool_type_varid]

##groups by detail and eliminates all sets of sample size <= sample_size
def eliminate_small_samples(df, sample_size = 1):
    df_out = df.copy()
    glogp = df_out.groupby('variedad_id').logprecio
    df_out['sample_size'] = glogp.transform(lambda x: x.size)
    df_out = df_out[df_out['sample_size'] > sample_size]
    return df_out

##eliminates outliers according to variance criterion on the prices
def eliminate_outliers_price(df, criterion = 0.05):
    df_out = df.copy()
    glogp = df_out.groupby('variedad_id').logprecio
    df_out['var_log'] = glogp.transform('var')
    df_out['mean_log'] = glogp.transform('mean') 
    df_out['criterio'] = df_out['var_log'] / ( (df_out['logprecio'] - df_out['mean_log'])**2  + 1e-12) + df_out.var_log.apply(lambda x: int(x == 0))
    df_out = df_out[df_out['criterio'] > criterion]
    return df_out


#TO DO
##eliminates outliers according to variance criterion on the price variations
##def eliminate_outliers_pricevariation(df):
##    df_out = df.copy()
##    df_out['year-month'] = df_out.fecha.apply(lambda x: '-'.join(x.split('-')[:-1] ) ) #standard format
##    glogp = df_out.groupby('detalle').logprecio
##    df_out['sample_size'] = glogp.transform(lambda x: x.size)
##    df_out = df_out[data_df['sample_size'] > 1]
##    
##    aggregate_df = df_out.groupby(['year-month', 'detalle', 'producto', 'producto_id', 'variedad_id']).precio.aggregate(['min', 'max', 'mean'])
##    aggregate_df = aggregate_df.reset_index().sort_values('fecha', kind = 'mergesort')
##    aggregate_df = aggregate_df.sort_values('detalle', kind = 'mergesort')
##    aggregate_df['monthly_percent_variation (mean)'] = aggregate_df['mean']/aggregate_df['mean'].shift(1) - 1
##    aggregate_df['monthly_percent_variation (mean)'] = (aggregate_df['monthly_percent_variation (mean)']
##                                                                                .where(aggregate_df['detalle'] == aggregate_df['detalle'].shift(1)
##                                                                                       & aggregate_df['fecha'] == aggregate_df['detalle'].shift(1)))
##    aggregate_df['fecha_gabriel'] = aggregate_df['year-month'].apply(lambda x: date(x + '-01') )
##    return df_out

        

########################################################## LOADING FILES ###########################################################
    
##    save_pickles(product_list = 'data.xlsx', id_list = 'producto_id.xlsx') ##Save files as pickles to retrieve them faster

data_df  = pd.read_excel('data.xlsx') ##Read file with data
##    data_df.to_pickle('data.pkl')
#data_df = pd.read_pickle('data.pkl')
producto_id = pd.read_excel('producto_id.xlsx', index_col = 0) ##Read file of product - product_id pairs
##    detalle_producto = pd.read_excel('product_detail.xlsx', index_col = 0) ##Read file of detail - product pairs
##    detalle_producto = detalle_producto['producto']

##    data_df, producto_id = load_pickles(product_list = 'data.pkl', id_list = 'producto_id.pkl') ##Load files from saved pickles
producto_id = producto_id['producto_id']
print(producto_id.head())

organizing_table = pd.read_excel('organizing_table.xlsx')

print('finished loading')

#####################################################################################################################################

data_df = eliminate_nodetail_or_noprice(data_df)

data_df['precio'] = data_df.precio.apply(lambda x: np.float64(x))

varid_producto = organizing_table[['variedad_id', 'producto']]
varid_producto = varid_producto.drop_duplicates()
varid_producto = pd.Series(data = varid_producto.producto.values, index = varid_producto.variedad_id.values)




#####################################################################################################################################


data_df['logprecio'] = np.log10(data_df.precio)

start_time = time.time()

##Outlier filter

##################################################### LABEL DATA WITH PRODUCT ####################################################


data_df['producto'] = data_df['variedad_id'].apply(lambda x: varid_producto[x])
data_df['producto_id'] = data_df['producto'].apply(lambda x: producto_id[x])

###################################################################################################

df_pre = data_df.copy()

for i in range(4):
    data_df = eliminate_small_samples(data_df, 1)
    data_df = eliminate_outliers_price(data_df, 0.1)

df_post = data_df.copy()

################################################### HERE COME THE PLOTS ##########################

source_pre = ColumnDataSource(df_pre)

menu_producto = Select(title = 'Producto', options = ['all'] + sorted(list(df_pre.producto.unique())) )

menu_varid = Select(title = 'Variedad id',
                                        options = ['all'] + sorted( [str(ident) for ident in df_pre.variedad_id.unique()], key = int) )

plot = figure()
plot.scatter(x = 'variedad_id', y ='logprecio', source = source_pre)

def callback_producto(attr, old, new):
    producto = menu_producto.value
    varid = menu_varid.value
    print(producto)
    print(varid)
    if producto == 'all':
        menu_varid.options = ['all'] + sorted( [str(ident) for ident in df_pre.variedad_id.unique()], key = int)
        source_pre.data = {col: df_pre[col] for col in df_pre.columns}

    else:
        menu_varid.options = ['all'] + sorted( [str(ident) for ident
                                                      in df_pre[df_pre.producto == producto].variedad_id.unique()],
                                                                        key = int)
        source_pre.data = {col: df_pre[col][df_pre.producto == producto] for col in df_pre.columns}
        
    menu_varid.value == 'all'

def callback_varid(attr, old, new):
    varid = menu_varid.value
    producto = menu_producto.value
    print(producto)
    print(varid)
    if varid == 'all':
        if producto == 'all':
            source_pre.data = {col: df_pre[col] for col in df_pre.columns}
        else:
            source_pre.data = {col: df_pre[col][df_pre.producto == producto] for col in df_pre.columns}
    else:
        source_pre.data = {col: df_pre[col][df_pre.variedad_id == int(varid)] for col in df_pre.columns}
        
    

menu_producto.on_change('value', callback_producto)
menu_varid.on_change('value', callback_varid)

layout = column(widgetbox(menu_producto, menu_varid), plot)
output_file('bokeh_plot.html')
curdoc().add_root(layout)


    

