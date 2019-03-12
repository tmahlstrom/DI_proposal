from numpy.random import rand
import numpy as np
from scipy import stats
import csv
import os
import pandas as pd
import math
import ast
import json
from itertools import cycle, islice

from bokeh.core.properties import value
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models import HoverTool, FactorRange, ColumnDataSource

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib import rc
import seaborn as sns 
from matplotlib.colors import ListedColormap
import matplotlib.style as style
from matplotlib.patches import Patch
from matplotlib.font_manager import FontProperties
from matplotlib.colors import LinearSegmentedColormap

plot_type = 'relative' # 'relative' vs 'absolute'
game_num = 4 #using game 4 (from DC_1_17) for presentation

def main():
    av_move_dict, ch_move_dict = configure_source_files()
    all_options_df = get_performance_df(av_move_dict, ch_move_dict)
    plot_performance(all_options_df)

def configure_source_files():
    with open("/Users/tylerahlstrom/Desktop/GitHub/DI_proposal/data/stockfish_performances_DC_1_17.csv", "r") as read_file:
        df = pd.read_csv(read_file)

    am_json_entry = df['available_moves_eval_w'][game_num]
    available_move_dict = json.loads(am_json_entry)
    cm_json_entry = df['chosen_moves_eval_w'][game_num]
    chosen_move_dict = json.loads(cm_json_entry)

    return available_move_dict, chosen_move_dict


def get_performance_df(av_move_dict, ch_move_dict):
    all_options_dict = {}
    print("Number of moves to plot: " + str(len(av_move_dict)))
    for move_num in av_move_dict:
        past_rank_considerations = [] #just to init for following for loop
        for move_option in av_move_dict[move_num]:
            temp_move_dict = av_move_dict[move_num][move_option]
            current_rank_consideration = int(temp_move_dict['rank'])
            while current_rank_consideration in past_rank_considerations:
                current_rank_consideration += 1
            past_rank_considerations.append(current_rank_consideration)

            rank_tag = str(current_rank_consideration)
            if len(rank_tag) == 1:
                rank_tag = "0" + rank_tag
            
            id_string = str(int(move_num) + 1) + '_' + rank_tag
            all_options_dict[id_string] = [0.0 for _ in ch_move_dict.keys()]
            all_options_dict[id_string][int(move_num)] = 1./float(ch_move_dict[move_num]['num_move_options'])
            all_options_dict[id_string].append(temp_move_dict['cp_score'])
            all_options_dict[id_string].append(temp_move_dict['mate_score'])
            all_options_dict[id_string].append(move_option == ch_move_dict[move_num]['move'])

    col_names = [str(m + 1) for m in range(len(ch_move_dict))]
    for i in range(len(col_names)):
        if len(col_names[i]) == 1:
            col_names[i] = "0"+ col_names[i]
        col_names[i] = 'move '+ col_names[i]
    col_names.append('cp_score')
    col_names.append('mate_score')
    col_names.append('was_chosen')

    df = pd.DataFrame.from_dict(all_options_dict, orient='index', columns= col_names)
    df = df.assign(sort_num = df.index.values)
    df['sort_num'] = df['sort_num'].apply(lambda x: int(x[:-3] + x[-2:]))
    df = df.sort_values(by = 'sort_num', ascending = False)

    # with open('test', 'w') as f:
    #     for line in df.to_csv(sep = '\t'):
    #         f.write(line)
    # f.close()

    return df



def plot_performance(df):
    style.use('seaborn-talk') 
    sns.set_style("white")
    sns.set_context("poster", font_scale=1.5,)
    font = {'fontname':'Adobe Hebrew'}
   

    cp_list = list(df['cp_score'])
    mate_list = list(df['mate_score'])
    chosen_list = list(df['was_chosen'])

    if plot_type == 'absolute':
        colors = get_colors(cp_list, mate_list, chosen_list)
    else:
        colors = get_neutral_colors(cp_list, chosen_list)
    

    exclude = ['sort_num', 'cp_score', 'mate_score', 'was_chosen']
    p = df.ix[:, df.columns.difference(exclude)].T.plot(kind='bar', stacked=True, color = colors, edgecolor = 'black', figsize=(24,8), grid = None, legend=False, linewidth = 1.5)
    plt.rcParams["font.size"] = 28
    plt.minorticks_off()
    #plt.setp(p, markerfacecolor='C0')
    x_ticks_int = [int(x) for x in range(len(df.ix[:, df.columns.difference(exclude)].columns))]
    x_ticks_str = [str(x+1) for x in range(len(df.ix[:, df.columns.difference(exclude)].columns))]
    
    plt.xticks(x_ticks_int, x_ticks_str, rotation='horizontal', fontsize=14, fontname = 'Lucida Console')
    plt.yticks([])

    if plot_type == 'absolute':
        title = "Absolute score of all move options in a single game"
    else:
        title = "Performance in a single game of chess: choice rank"

    plt.title(title, loc = 'center', y=0.99, bbox=dict(facecolor='white', edgecolor='black', boxstyle='square', linewidth = 1.0), fontsize=34, **font)
    plt.xlabel("Turn number", fontsize=24, **font)
    plt.ylabel("Relative\nmove\noption\nstrength", rotation = 'horizontal', horizontalalignment = 'left', labelpad= 90, fontsize=24, **font)
    plt.xlim(-0.75, x_ticks_int[-1] + 0.75)
    plt.ylim(0.0, 1.1)

    ax = plt.subplot(111)
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    
    map_colors = [(0, 51./255., 102./255.), (.7, .6, .7), (102./255., 0, 25./255.)] 
    cmap_name = 'my_custom_cmap'
    cmap = LinearSegmentedColormap.from_list(cmap_name, map_colors, N=9)

    if plot_type == 'absolute':
        #cmap = matplotlib.cm.get_cmap('coolwarm')
        legend_elements = [Patch(facecolor=[0, 51./255., 102./255.], edgecolor='black',
                            label='Strong move', linewidth = 1.0),
                            Patch(facecolor=[102./255., 0, 25./255.], edgecolor='black',
                            label='Weak move', linewidth = 1.0)]
        ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 18, 'family':'Adobe Hebrew'}, labelspacing = 1.5)
    if plot_type == 'relative':
        legend_elements = [Patch(facecolor=[218.0/255,165/255.0,32.0/255, 1.0], edgecolor='black',
                            label='Chosen move \noption', linewidth = 1.0), 
                            Patch(facecolor=[0.0, 0.0, 0.0, 0.6], edgecolor='black',
                            label='Unchosen move \noption', linewidth = 1.0)]
        ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 18, 'family':'Adobe Hebrew'}, labelspacing = 1.0)

    # plt.legend(handles=legend_elements, loc='top')
    plt.show()


def get_neutral_colors(score_list, chosen_list):
    base_color = [0,0,0, 0.0]
    colors = []
    for _, chosen in zip(score_list, chosen_list):
        alpha = 0.6
        if chosen:
            color = [218.0/255,165/255.0,32.0/255, 1.0]
            colors.append(color)
        else:
            color = base_color
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
    return colors




def get_colors(score_list, mate_list, chosen_list):
    colors = [(0, 51./255., 102./255.), (.7, .6, .7), (102./255., 0, 25./255.)] 
    #n_bins = [3, 6, 10, 100]
    cmap_name = 'my_custom_cmap'
    cmap = LinearSegmentedColormap.from_list(
        cmap_name, colors, N=9)
    #cmap = matplotlib.cm.get_cmap('coolwarm')
    colors = []
    int_helper1 = -1
    int_helper2 = 1

    for cp, mate, chosen in zip(score_list, mate_list, chosen_list):
        alpha = 1.0 #the non-chosen alpha
        if chosen:
            alpha = 1.0

        if mate is not None:
            if mate[0] == 'A':
                color = cmap(0.0 *int_helper2)
                color = (color[0] , color[1], color[2], alpha)
                colors.append(color)
            elif mate[0] == 'D':
                color = cmap(0.9 *int_helper2)
                color = (color[0] , color[1], color[2], alpha)
                colors.append(color)

        elif cp < 1000*int_helper1:
            color = cmap(1.0 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            #color[:, 3] = alpha
            colors.append(color)

        elif cp < 900*int_helper1:
            color = cmap(0.9 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 800*int_helper1:
            color = cmap(0.8 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 600*int_helper1:
            color = cmap(0.7 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 400*int_helper1:
            color = cmap(0.6 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 200*int_helper1:
            color = cmap(0.5 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 150*int_helper1:
            color = cmap(0.4 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 100*int_helper1:
            color = cmap(0.3 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 70*int_helper1:
            color = cmap(0.2 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp < 30*int_helper1:
            color = cmap(0.1 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        elif cp is not None:
            color = cmap(0.0 *int_helper2)
            color = (color[0] , color[1], color[2], alpha)
            colors.append(color)
        else:
            print("lost color here" + str(cp) + str(mate) + str(chosen))
        
    return colors


    #print(data)
    # y-axis in bold

    # rc('font', weight='bold')
    
    # # Values of each group
    # bars1 = [12, 28, 1, 8, 22]
    # bars2 = [28, 7, 16, 4, 10]
    # bars3 = [25, 3, 23, 25, 17]
    
    # # Heights of bars1 + bars2 (TO DO better)
    # bars = [40, 35, 17, 12, 32]
    
    # # The position of the bars on the x-axis
    # r = [0,1,2,3,4]
    
    # # Names of group and bar width
    # names = ['A','B','C','D','E']
    # barWidth = 1
    
    # # Create brown bars
    # plt.bar(r, bars1, color='#7f6d5f', edgecolor='white', width=barWidth)
    # # Create green bars (middle), on top of the firs ones
    # plt.bar(r, bars2, bottom=bars1, color='#557f2d', edgecolor='white', width=barWidth)
    # # Create green bars (top)
    # plt.bar(r, bars3, bottom=bars, color='#2d7f5e', edgecolor='white', width=barWidth)
    
    # # Custom X axis
    # plt.xticks(r, names, fontweight='bold')
    # plt.xlabel("group")
    
    # # Show graphic
    # plt.show()



def test():
    sns.set()
    df = pd.DataFrame(columns=["App","Feature1", "Feature2","Feature3",
                           "Feature4","Feature5",
                           "Feature6","Feature7","Feature8"], 
                  data=[["SHA",0,0,1,1,1,0,1,0],
                        ["LHA",1,0,1,1,0,1,1,0],
                        ["DRA",0,0,0,0,0,0,1,0],
                        ["FRA",1,0,1,1,1,0,1,1],
                        ["BRU",0,0,1,0,1,0,0,0],
                        ["PAR",0,1,1,1,1,0,1,0],
                        ["AER",0,0,1,1,0,1,1,0],
                        ["SHE",0,0,0,1,0,0,1,0]])
    df = df.set_index('App').reindex(df.set_index('App').sum().sort_values().index, axis=1)
    print(df)
    df.T.plot(kind='bar', stacked=True, colormap=ListedColormap(sns.color_palette("GnBu", 10)), figsize=(12,6))
    plt.show()

    

if __name__ == '__main__':
    main()