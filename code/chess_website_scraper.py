import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import csv


def main():

    driver = webdriver.Firefox()


    for i in range (200, 400): #range will be 0,len(list_of_players)

        url = "https://www.chess.com/leaderboard/live/rapid?page=" + str(i * 100)
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")
        page_data1 = soup.find_all("ul", {"class": "game-stats hide-on-hover"})
        page_data2 = soup.find_all("td", {"class": "text-right"})

        accs_stats_page = []
        acc_stats_pre = ""

        for x in range (3, 50):
            try:
                acc_stats_pre = (page_data1[x].text)
                acc_stats = (acc_stats_pre.splitlines())
                acc_stats[0] = page_data2[1+x*3].text
                accs_stats_page.append(acc_stats)
            except:
                continue

        print(accs_stats_page)

        acc_records_file = open('chess_acc_records.txt', 'a')
        writer = csv.writer(acc_records_file, delimiter=',', quotechar='"')
        for entry in accs_stats_page:
            writer.writerow(entry)

        acc_records_file.close()
    driver.close()
    # page_data = soup.find_all("div", {"class": "winLossContainer"})
    # data_set = []
    # for item in page_data:
    #     data_set.append(item.text)
    # data_set2 = data_set[0].split('\n')
    # while '' in data_set2:
    #     data_set2.remove('')
    # wins = data_set2[0][:-6]
    # loses = data_set2[1][:-8]
    # try:
    #     percentage = str(round((int(wins)/(int(wins) + int(loses)) * 100), 2))
    # except:
    #     percentage = 100.00
    # list_of_new_players[x].append(wins)
    # list_of_new_players[x].append(loses)
    # list_of_new_players[x].append(percentage)
    # #print(list_of_players[x])
    # player_update_temp.write(str(list_of_new_players[x]) + ", ")  # , end='', flush=True)
    # # print(str(game_results) + ", ", end='', flush=True)
    # player_update_temp.flush()


    ####

if __name__ == '__main__':
  main()