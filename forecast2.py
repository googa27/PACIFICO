import openpyxl as pyxl
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import itertools as itr
import time
import os
import datetime
import xlsxwriter
from sklearn import linear_model, feature_selection
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import GaussianNB, MultinomialNB, BernoulliNB
from sklearn.neural_network import MLPClassifier
import time
import numbers
import scipy.optimize as opt
import statsmodels.api as sm
import  pandas.plotting as pdplt
import seaborn as sns

#sns.set()


################################################## AUXILIARY FUNCTIONS #############################################################

def make_date(x):
    if type(x) == str:
        l = x.split('-')
        year = int(l[0])
        month = int(l[1])
        return datetime.date(year, month, 1)
    return x

def make_time(x):
    if type(x) == str:
        l = x.split('-')
        year = int(l[0])
        month = int(l[1])
        return pd.Timestamp(year, month, 1)
    if type(x) == datetime.date:
         return pd.Timestamp(x.year, x.month, 1)
    return x

def ecdf(data):
    n = len(data)
    x = np.sort(data)
    y = np.arange(1, n+1)/n
    
    return x, y

make_date = np.vectorize(make_date)
make_time = np.vectorize(make_time)


################################################ BIG SCARY REGRESSION FUNCTIONS #################################################

## ALL IMPUTS HAVE TO BE RAW DATAFRAMES   

###
#returns all regressions of size k
def get_all_noneg(x, y, k): #fill with mean after
    results_k = []
      
    for combo in itr.combinations(x.columns, k):
        lcombo = list(combo)

        minimal_length = len(lcombo) + 1
        
        xy = pd.concat([x[lcombo], y], axis = 1)
        xy.dropna(axis = 0, how = 'any', inplace = True)

        x_nonans = xy.iloc[:, :-1]
        y_nonans = xy.iloc[:, -1]

        x_regression= sm.add_constant(x_nonans)

        if len(x_regression) > minimal_length: #to prevent overdetermined system
            model = sm.OLS(y_nonans, x_regression)
            result = model.fit()
            results_k.append(result)

    if len(results_k)>0:
        print(len(results_k))
            
    results_k = [result for result in results_k if (result.params.iloc[1:] >0 ).all()]
    return results_k
        
#returns a list with the best n regressions, sorted by r2_adj
def all_subsets_bestn_regression(x, y, n):
    all_results = [reg for k in range(len(x.columns) + 1) for reg in get_all_noneg(x, y, k)]
    all_results_nonan = [result for result in all_results if result]
    out = sorted(all_results_nonan, key = lambda x: x.rsquared_adj, reverse = True)
    if len(out) > n:
        return out[:n] ##return the n best results
    return out

###

def igal_plot(best_dic):
    r2_adj_plot = {key + " " + str(int(best_dic[key].nobs)): best_dic[key].rsquared_adj for key in best_dic}
    sorted_r2_adj = sorted(r2_adj_plot.items(), key = lambda x: x[1], reverse = True)
    graph_data = [x[1] for x in sorted_r2_adj]
    labels = [x[0] + str() for x in sorted_r2_adj]
    ind = np.arange(len(labels))
    fig, ax = plt.subplots()
    rects = ax.bar(ind, graph_data)
    ax.grid(True)
    ax.set_xticks(ind)
    ax.set_xticklabels(labels, rotation = 90)
    ax.set_ylabel("r2_adj")

    plt.show()


######################################################### DATA IMPORTS #############################################################

t0 = time.time()

df_data = pd.read_excel('data_monthly.xlsx').pivot_table(index = 'year-month',
                                                                          columns = ['producto', 'variedad_id'],
                                                                          values = 'var_ipc')
df_ipc = pd.read_excel('IPC Productos - variaciones.xlsx').pivot_table(index = 'fecha',
                                                                          columns = 'producto',
                                                                          values = 'var_ipc')

organizing_table = pd.read_excel('organizing_table.xlsx')


print('----------', (time.time() - t0),  'seconds---------')


#################################################### DETAILS AND ADJUSTEMENTS ####################################################

df_data.index.name = 'fecha'

df_data.index = make_time(df_data.index)
df_data.index.name = 'fecha'

varid_detalle = organizing_table[['variedad_id', 'detalle']]
varid_detalle = varid_detalle.drop_duplicates()
varid_detalle = pd.Series(data = varid_detalle.detalle.values, index = varid_detalle.variedad_id.values)


###################################################### REGRESSIONS FOR ALL!!! ######################################################

best_n_dic = {}
n = 4 #number of best regressions desired

t0 = time.time()

for product in df_data.columns.levels[0]:
    x = df_data[product]
    y = df_ipc[product]

    best_n_dic[product] = all_subsets_bestn_regression(x, y, n)

print('----------', (time.time() - t0),  'seconds---------')

best_dic = {product: best_n_dic[product][0] for product in best_n_dic}

################################################## A FEW PLOTS OF THE DATA #########################################
 
r2_adj_dic = {key: best_dic[key].rsquared_adj for key in best_dic}
coef_dic = {key: best_dic[key].params for key in best_dic}

r2 = np.array( [best_dic[key].rsquared for key in best_dic]  )
r2_adj = np.array( [best_dic[key].rsquared_adj for key in best_dic] )

x, y = ecdf(r2_adj)
_ = plt.plot(x, y)
plt.xlabel('r2_adj')
plt.ylabel('percentage of products')
plt.show()

igal_plot(best_dic)

####################################################################################################################

t0 = time.time()

products_dic = {product : pd.concat([reg.params.index.to_series()
                                      for reg in best_n_dic[product]]).drop_duplicates().reset_index(drop = True)
                for product in best_n_dic.keys() if r2_adj_dic[product] >= r2_adj_dic["PAN"]}

df_products = pd.DataFrame(products_dic)
df_products = df_products.loc[1:].stack().reset_index().drop("level_0", axis = 1).sort_values(0)
df_products.columns = ["producto", "variedad_id"]
df_products["detalle"] = df_products["variedad_id"].apply(lambda x: varid_detalle[x])

writer = pd.ExcelWriter('productos_encuestador.xlsx', engine = 'xlsxwriter')
df_products.to_excel(writer, index = False)
writer.save()

###################################################### PASS RESULTS TO EXCEL AND PLOT ##############################

ipc_both = []

for product in df_data.columns.levels[0]:
    x, y = best_dic[product].fittedvalues, df_ipc[product]
    x.name = 'var_ipc_predictions'
    y.name = 'var_ipc_ine'
    xy = pd.concat([x, y], axis = 1)

    ## PLOTTING AND SAVING
    xy.var_ipc_ine.plot()
    xy.var_ipc_predictions.plot()
    plt.legend()
    plt.title(product)
    plt.ylabel('variacion porcentual mensual')
    plt.savefig('figures_predictions/' + product)
    plt.clf()
    
    
    xy['producto'] = product
    ipc_both.append(xy)
    
ipc_both = pd.concat(ipc_both)

writer = pd.ExcelWriter('predictions.xlsx', engine = 'xlsxwriter')
ipc_both.to_excel(writer, index = True)
writer.save()

print('----------', (time.time() - t0),  'seconds---------')
