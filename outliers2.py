import openpyxl as pyxl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools as itr
import time
import os
import datetime
import xlsxwriter
import time
import numbers
#import editdistance as ed
import sys
print("started bokeh")
from bokeh.plotting import figure, output_file, show
from bokeh.charts import Histogram
from bokeh.io import curdoc
from bokeh.layouts import column, row, widgetbox
from bokeh.models import ColumnDataSource, Slider, Select


print("ended bokeh")

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
    bool_precio = df['precio'] == df['precio']
    bool_null_price = ~(df['precio'] == 0)
    bool_detalle = df['detalle'] == df['detalle']
    bool_varid = df['variedad_id'] == df['variedad_id']
    bool_type_precio = df['precio'].apply(lambda x : isinstance(x, numbers.Number))
    bool_type_detalle = df['detalle'].apply(lambda x : isinstance(x, str))
    bool_type_varid = df['variedad_id'].apply(lambda x : isinstance(x, numbers.Number))
    return df[bool_precio & bool_null_price & bool_detalle & bool_varid
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

################################################################################################################################

def sort_plot(s1, s2):

    y1 = sorted(s1.values, reverse = True)
    y2 = sorted(s2.values, reverse = True)

    x1 = np.arange(len(y1))
    x2 = np.arange(len(y2))
    
    fig = plt.figure()
    p1 = fig.add_subplot(221)
    p2 = fig.add_subplot(222)
    p3 = fig.add_subplot(223)
    p4 = fig.add_subplot(224)
    p1.set_title("before filter")
    p2.set_title("after filter")
    p3.set_title("before filter")
    p4.set_title("after filter")
    p1.bar(x1, y1)
    p2.bar(x2, y2)
    p3.hist(y1, bins = int((len(y1))**0.6))
    p3.hist(y2, bins = int((len(y1))**0.6))
    plt.show()
        


########################################################## LOADING FILES ###########################################################

##    save_pickles(product_list = 'data.xlsx', id_list = 'producto_id.xlsx') ##Save files as pickles to retrieve them faster

data_df  = pd.read_excel('data.xlsx') ##Read file with data
producto_id = pd.read_excel('producto_id.xlsx', index_col = 0) ##Read file of product - product_id pairs

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






##################################################### LABEL DATA WITH PRODUCT ####################################################   

data_df['producto'] = data_df['variedad_id'].apply(lambda x: varid_producto[x])
data_df['producto_id'] = data_df['producto'].apply(lambda x: producto_id[x])

#####################################################################################################################################

data_df['logprecio'] = np.log10(data_df.precio)

df_prefilter = data_df.copy()

start_time = time.time()

##Outlier filter
for i in range(4):
    data_df = eliminate_small_samples(data_df, 1)
    data_df = eliminate_outliers_price(data_df, 0.1)

df_postfilter = data_df.copy()

########################################################### VERIFICATION PLOT ######################################

##    s1 = df_prefilter.logprecio[df_prefilter.producto == "CARNE DE VACUNO"]
##    s2 = df_postfilter.logprecio[df_postfilter.producto == "CARNE DE VACUNO"]
##    sort_plot(s1, s2)

# Create two dropdown Select widgets: select1, select2

source_prefilter = ColumnDataSource(df_prefilter)

source_postfilter = ColumnDataSource(df_postfilter)

menu_producto = Select(title='Producto', options=["all"] + sorted(list(df_prefilter.producto.unique())),
                       value='all')
menu_variedad = Select(title='Variedad_id', options=["all"] + sorted([str(index) for index
                                                                      in df_prefilter.variedad_id.unique()],
                                                                     key = lambda x: int(x)), value='all')

plot = Histogram(df_prefilter, "logprecio", title = menu_producto.value + menu_variedad.value)

# Define a callback function: callback
def callback_producto(attr, old, new):
    # If select1 is 'A' 
    if menu_producto.value == 'all':

        plot = Histogram(df_prefilter, "logprecio", title = menu_producto.value + menu_variedad.value)

        # Set select2 options to ['1', '2', '3']
        menu_variedad.options = ["all"] + sorted([str(index) for index
                                                    in df_prefilter.variedad_id.unique()],
                                            key = lambda x: int(x))
        
    else:
        # Set select2 options to ['100', '200', '300']
        plot = Histogram(df_prefilter[df_prefilter.producto == menu_producto.value], "logprecio",
                         title = menu_producto.value + menu_variedad.value) ###THIS IS NOT WORKING
        menu_variedad.options = ["all"] + sorted([str(index) for index
                                                   in df_prefilter[df_prefilter.producto == menu_producto.value]
                                                    .variedad_id.unique()],key = lambda x: int(x))
    menu_variedad.value = 'all'

# Attach the callback to the 'value' property of select1
menu_producto.on_change('value', callback_producto)

# Create layout and add to current document
layout = row(widgetbox(menu_producto, menu_variedad), plot)
curdoc().add_root(layout)

########################################################### MONTH AVERAGE ########################################################
data_df['year-month'] = data_df.fecha.apply(lambda x: pd.Period(x, 'M') )
aggregate_df = data_df.groupby(['year-month', 'producto', 'producto_id', 'variedad_id']).precio.aggregate(['min', 'max', 'mean'])
aggregate_df = aggregate_df.reset_index().sort_values('year-month', kind = 'mergesort')
aggregate_df = aggregate_df.reset_index().sort_values('variedad_id', kind = 'mergesort')
aggregate_df['var_ipc'] = aggregate_df['mean']/aggregate_df['mean'].shift(1) - 1


#####################
aggregate_df['year'] = aggregate_df['year-month'].apply(lambda x: x.year)
aggregate_df['month'] = aggregate_df['year-month'].apply(lambda x: x.month)
aggregate_df['delta_year'] = aggregate_df.year - aggregate_df.year.shift(1)
aggregate_df['delta_month'] = aggregate_df.month - aggregate_df.month.shift(1)
case_1 = aggregate_df.delta_year.apply(lambda x: x == 0) & aggregate_df.delta_month.apply(lambda x: x == 1)
case_2 = aggregate_df.delta_year.apply(lambda x: x == 1) & aggregate_df.delta_month.apply(lambda x: x == -11)
aggregate_df['consec_dates'] = case_1 | case_2
aggregate_df['var_ipc'] = (aggregate_df['var_ipc'].where( (aggregate_df['variedad_id'] == aggregate_df['variedad_id'].shift(1))
                                                                                   & aggregate_df.consec_dates) ) 

######################################################## SAVE MONTHLY FILE ########################################################

start_time = time.time()

writer = pd.ExcelWriter('data_monthly.xlsx', engine = 'xlsxwriter')
aggregate_df.to_excel(writer, index = False)
writer.save()

print("--- %s seconds ---" % (time.time() - start_time))

    

