import matplotlib.pyplot as plt
from numpy.random import rand
import matplotlib
import numpy as np
from scipy import stats
import csv


def main():
    with open('chess_acc_records.csv', 'r') as f:
        reader = csv.reader(f)
        data_list = list(reader)

    x = []
    y = []

    for i in range (0, len(data_list)):
        games_played = int(int(data_list[i][1]) + int(data_list[i][2]))
        if games_played == 0:
            pass
        win_percentage = 0
        try:
            win_percentage = float(int(data_list[i][1]) / (games_played)) * 100
        except:
            win_percentage = float(100)
        if games_played >= 1 and games_played < 15:
            #print(str(data_list[i][0]) + " " + str(win_percentage))
            x.append(int(data_list[i][0]))
            y.append(win_percentage)
        else:
            pass

    x = np.array(x)
    y = np.array(y)

    color = 'r'
    scale = 1.0


    #plt.legend()
    plt.scatter(x,y, s=scale, c=color, marker = ",", lw=0, alpha = 0.5, label = '$\mathregular{}$accounts with # games played: <15')
    #plt.scatter(x, y, c="g", alpha=0.5, marker=r'$\clubsuit$',label="Luck")
    m, b = np.polyfit(x, y, 1)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    plt.plot(x, slope*x +intercept, '-', c = color, label = '$\mathregular{}$slope = ' + '%1.2E' % slope)
    #plt.legend(('data', 'line-regression r={}'.format(r_value)), 'best')

    #############################################################################

    x = []
    y = []

    for i in range (0, len(data_list)):
        games_played = int(int(data_list[i][1]) + int(data_list[i][2]))
        if games_played == 0:
            pass
        win_percentage = 0
        try:
            win_percentage = float(int(data_list[i][1]) / (games_played)) * 100
        except:
            win_percentage = float(100)
        if games_played >= 15 and games_played < 100:
            #print(str(data_list[i][0]) + " " + str(win_percentage))
            x.append(int(data_list[i][0]))
            y.append(win_percentage)
        else:
            pass

    x = np.array(x)
    y = np.array(y)

    color = 'y'
    scale = 1.0


    #plt.legend()

    plt.scatter(x,y, s=scale, c=color, marker = ",", lw=0, alpha = 1.0, label = '$\mathregular{}$accounts with # games played: 15-100')
    m, b = np.polyfit(x, y, 1)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    plt.plot(x, slope*x +intercept, '-', c = color, label = '$\mathregular{}$slope = ' + '%1.2E' % slope)
    #plt.legend(('data', 'line-regression r={}'.format(r_value)), 'best')

    # #########################################################################

    x = []
    y = []

    for i in range (0, len(data_list)):
        games_played = int(int(data_list[i][1]) + int(data_list[i][2]))
        if games_played == 0:
            pass
        win_percentage = 0
        try:
            win_percentage = float(int(data_list[i][1]) / (games_played)) * 100
        except:
            win_percentage = float(100)
        if games_played >= 100:
            #print(str(data_list[i][0]) + " " + str(win_percentage))
            x.append(int(data_list[i][0]))
            y.append(win_percentage)
        else:
            pass

    x = np.array(x)
    y = np.array(y)

    color = 'b'
    scale = 1.0


    #plt.legend()

    plt.scatter(x,y, s=scale, c=color, marker = ",", lw=0, alpha = 0.5, label = '$\mathregular{}$accounts with # games played: >100')
    m, b = np.polyfit(x, y, 1)

    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    plt.plot(x, slope*x +intercept, '-', c = color, label = '$\mathregular{}$slope = ' + '%1.2E' % slope)
    #plt.legend(('data', 'line-regression r={}'.format(r_value)), 'best')

    # ##########################################################################


    # x = []
    # y = []

    # for z in range (0, len(data_list)):
    #     if data_list[z][2] >= 100 and data_list[z][2] < 300:
    #         x.append(data_list[z][0])
    #         y.append(data_list[z][1])
    #     else:
    #         pass

    # x = np.array(x)
    # y = np.array(y)

    # color = 'b'
    # scale = 1.0



    # plt.scatter(x,y, s=scale, c=color, marker = ",", lw=0, alpha = 0.5, label = '$\mathregular{}$100-299 games' + ", n= " +str(len(x)))

    # slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    # plt.plot(x, slope*x +intercept, '-', c = color, label = '$\mathregular{r^2}$' + '=%.4f' % r_value)

    # ##########################################################################

    # x = []
    # y = []

    # for z in range (0, len(data_list)):
    #     if data_list[z][2] >= 300:
    #         x.append(data_list[z][0])
    #         y.append(data_list[z][1])
    #     else:
    #         pass

    # x = np.array(x)
    # y = np.array(y)

    # color = 'k'
    # scale = 1.0


    # plt.scatter(x,y, s=scale, c=color, marker = ",", lw=0, label = '$\mathregular{}$300+ games' + ", n= " +str(len(x)))

    # slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    # plt.plot(x, slope*x +intercept, '-', c = color, label = '$\mathregular{r^2}$' + '=%.4f' % r_value)









    plt.xlabel('$\mathregular{}$Elo (skill rating)', size = 18)
    plt.ylabel('$\mathregular{}$Win%', size = 18)
    plt.title('$\mathregular{}$Elo vs Win%', size = 24)



    # plt.legend()
    leg = plt.legend(loc = 2, ncol = 2, scatterpoints=5, prop = {'size':16}, markerscale = 2.5, fancybox = True)
    leg.get_frame().set_alpha(1.0)


    plt.grid(True)
    plt.show()






if __name__ == '__main__':
  main()