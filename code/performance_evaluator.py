#!/bin/sh
import chess
import chess.uci
import chess.pgn
import os
import csv
import json
from numpy import array
import numpy as np
import math
import time
from datetime import datetime
from multiprocessing import Pool
import sys
from twilio.rest import Client


skip_games = 0 #from file now #320 #305 
batch_size = 56
num_batches = 30
sec_eval_per_move = 0.3
num_processors = 7
multiprocess_flag = True
print_to_console = True

sys.setrecursionlimit(15000)

text_notification_on = False
t_acc = 'AC4400f5964a54435cd2cba080478cb9c9'
t_tok = '96af49f32cd628d9aa50439b2d4ea944'
t_cli = Client(t_acc, t_tok)
t_num = '+12028512902'
my_p = '+16515874056'

#writing_file = "/Users/tylerahlstrom/Documents/GitHub/DI_Proposal/data/stockfish_performances_1sec_TEST.csv"
writing_file = "stockfish_performances_DC.csv"
#csv_columns = ['elo', 'acc_name', 'opp_elo', 'opp_acc_name', 'date', 'time', 'piece_color', 'opening', 'eco', 'result', 'rating_change', 'opp_rating_change', 'event', 'engine_eval_seconds', 'game_time_settings', 'termination', 'chosen_moves_eval', 'available_moves_eval', 'opp_chosen_moves_eval', 'opp_available_moves_eval', 'site']
csv_columns = ['elo_w', 'elo_b', 'acc_name_w', 'acc_name_b', 'date', 'time', 'opening', 'eco', 'result', 'rating_change_w', 'rating_change_b', 'event', 'engine_eval_seconds', 'game_time_settings', 'termination', 'chosen_moves_eval_w', 'chosen_moves_eval_b', 'available_moves_eval_w', 'available_moves_eval_b', 'site']
#pgns_all_path = "/Users/tylerahlstrom/Documents/GitHub/DI_Proposal/data/lichess_db_standard_rated_2017-03.pgn"
pgns_all_path = "lichess_db_standard_rated_2017-04.pgn"
skip_games_file = "skip_games_post.txt"






def main():
    if print_to_console:
        print("Preparing files")
    start_time = datetime.now()
    prepare_csv_file()

    
    num_games_to_skip, pgns = prepare_pgns()
    progress_count = 0


    for _ in range (num_batches):

        raw_games = []
        suitable_games = 0
        while suitable_games < batch_size:
            pgn = chess.pgn.read_game(pgns)
            game_info_dict = pgn.headers
            if "Event" in game_info_dict and game_info_dict["Event"] == "Rated Classical game":
                raw_games.append(pgn)
                suitable_games += 1
        multiprocess_batch(raw_games, multiprocess_flag)
        progress_count += batch_size

        overwrite_skip_games_file(progress_count+num_games_to_skip)

        message = "Games evaluated: " + str(progress_count)
        print(message)
        if (text_notification_on):
            send_text_notification(message)
    end_time = datetime.now()
    if print_to_console:
        print("Process duration: ", (end_time - start_time))


def prepare_csv_file():
    
    with open(writing_file, 'a') as csvfile:
        if os.stat(writing_file).st_size == 0:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()

    
    

def prepare_pgns():
    pgns = open(pgns_all_path)
    num_to_skip = 0
    with open(skip_games_file, 'r+') as skipfile:
        data = skipfile.readline()
        if (data):
            num_to_skip = int(data) 
        else: 
            print("Need to create skip games file")
    if num_to_skip > 0:
        pgns = skip_to_game(pgns, num_to_skip)
    if print_to_console:
        print("starting at game: ", num_to_skip + 1)
    return num_to_skip, pgns


def skip_to_game(pgns, num_to_skip):
    offsets = chess.pgn.scan_offsets(pgns)
    for i in range(num_to_skip):
        book_mark = next(offsets)
        if i == (num_to_skip - 1):
            pgns.seek(book_mark)
    return pgns

    
    # offsets = chess.pgn.scan_offsets(pgn_file)
    # book_mark = next(offsets)
    # for i in range(num_to_skip):
            # for _ in range (num_games_to_skip):
        # chess.pgn.read_game(pgns)
        # book_mark = pgn_file.tell()
        # pgn_file.seek(book_mark)
        # chess.pgn.skip_game(handle)
    #return pgns
        # book_mark = next(offsets)
        # if i == (num_to_skip - 1):
        #     pgn_file.seek(book_mark)

def get_skip_amount():
    with open(skip_games_file, 'r+') as skipfile:
        data = skipfile.readline()
        if (data):
            skip_games = int(data) 
        else: 
            print("Need to create skip games file")
    return skip_games


def multiprocess_batch(raw_games, multiprocess = True):
    if multiprocess:
        with Pool(processes = num_processors) as pool:
            # time.sleep( 5 )
            #pool = Pool(num_processors)
            pool.map(evaluate_game,raw_games)
            # time.sleep( 5 )
            pool.close()
            # time.sleep( 5 )
            pool.join()
            # time.sleep( 5 )
    else:
        for game in raw_games:
            evaluate_game(game)


def evaluate_game(game):
    performance = get_performance_dict(game)
    if not performance:
        return
    
    write_dict_to_csv(writing_file, csv_columns, performance)
    # for performance_dict in performance: 
    #     write_dict_to_csv(writing_file, csv_columns, performance_dict)


def get_performance_dict(game): 
    perf = {}

    if game is None:
        return perf
    
    engine, handler = initiate_engine_and_handler()
    board = game.board()
    engine.position(board)

    #wp = {}     #white perforamnce
    #bp = {}     #black performance
    #wp, bp = add_relevant_game_details(game, wp, bp)

    perf = {}
    perf = add_relevant_game_details(game, perf)

    wp_available_moves = []   #list of dictionaries containing info about each avaiable move at each (ordered) turn
    bp_available_moves = []

    wp_chosen_moves = []   #list of dictionaries containing info about each (ordered) chosen move
    bp_chosen_moves = []

    cp_eval, mate_eval = get_abs_board_evaluation(engine, handler, board)

    for move in game.main_line():

        
        move_options_dict = get_options_eval_dict(board, cp_eval, mate_eval, engine, handler)

        chosen_move_info_dict = {'move': str(move), 'move_rank': move_options_dict[str(move)]['rank'], 'num_move_options': len(move_options_dict), 'cp_score': move_options_dict[str(move)]['cp_score'], 'mate_score': move_options_dict[str(move)]['mate_score']}

        if board.turn == chess.WHITE:
            wp_available_moves.append(move_options_dict)
            wp_chosen_moves.append(chosen_move_info_dict)

        elif board.turn == chess.BLACK:
            bp_available_moves.append(move_options_dict)
            bp_chosen_moves.append(chosen_move_info_dict)

        cp_change = chosen_move_info_dict['cp_score']
        if cp_change is not None:
            if board.turn == chess.BLACK: 
                cp_change = -cp_change
            if cp_eval is not None:
                cp_eval += cp_change
            else:
                cp_eval = cp_change
        else:
             cp_eval = None

        mate_change = chosen_move_info_dict['mate_score']
        if mate_change is not None:
            mate_change = int(mate_change[3:])
            if board.turn == chess.BLACK: 
                mate_change = -mate_change
            if mate_eval is not None:
                mate_eval += mate_change
            else:
                mate_eval = mate_change
        else:
             mate_eval = None

        board.push(move)
        engine.position(board)


    perf["available_moves_eval_w"] = json.dumps({v: k for v, k in enumerate(wp_available_moves)})
    perf["chosen_moves_eval_w"] = json.dumps({v: k for v, k in enumerate(wp_chosen_moves)})
    perf["available_moves_eval_b"] = json.dumps({v: k for v, k in enumerate(bp_available_moves)})
    perf["chosen_moves_eval_b"] = json.dumps({v: k for v, k in enumerate(bp_chosen_moves)})

    # print(json.dumps({v: k for v, k in enumerate(wp_available_moves)}, indent = 2))
    # print(json.dumps({v: k for v, k in enumerate(wp_chosen_moves)}, indent = 2))

    # perf["available_moves_eval_w"] = wp_available_moves
    # perf["chosen_moves_eval_w"] = wp_chosen_moves
    # perf["available_moves_eval_b"] = bp_available_moves
    # perf["chosen_moves_eval_b"] = bp_chosen_moves

    # wp["available_moves_eval"] = wp_available_moves
    # wp["chosen_moves_eval"] = wp_chosen_moves
    # wp["opp_available_moves_eval"] = bp_available_moves
    # wp["opp_chosen_moves_eval"] = bp_chosen_moves
    
    # bp["available_moves_eval"] = bp_available_moves
    # bp["chosen_moves_eval"] = bp_chosen_moves
    # bp["opp_available_moves_eval"] = wp_available_moves
    # bp["opp_chosen_moves_eval"] = wp_chosen_moves

    return perf


def get_abs_board_evaluation(engine, handler, board):
    engine.go(movetime=sec_eval_per_move*1000)
    new_cp_eval = handler.info["score"][1].cp
    new_mate_eval = handler.info["score"][1].mate
    if board.turn == chess.BLACK:
        if new_cp_eval is not None:
            new_cp_eval = -new_cp_eval
        if new_mate_eval is not None:
            new_mate_eval = -new_mate_eval
    return new_cp_eval, new_mate_eval


def get_options_eval_dict(board, actual_cp_eval, actual_mate_eval, engine, handler):
    temp_options_list = []
    for move in board.legal_moves:
        board.push(move) #temporarily make the move
        engine.position(board)
        hyp_cp_eval, hyp_mate_eval = get_abs_board_evaluation(engine, handler, board) # not board.turn because it's not actually whose turn it is
        board.pop() #unmake the move
        engine.position(board)
        cp_merit, mate_merit = get_move_quality(board.turn, actual_cp_eval, actual_mate_eval, hyp_cp_eval, hyp_mate_eval)
        temp_options_list.append([move, cp_merit, mate_merit])

    temp_options_list = rank_options(temp_options_list)
    #temp_options_list.sort(key=lambda x: -float(x[1])) # this is probably going to need to be it's own function, sorting mate scenarios
    options_dict = {}
    for i in range (len(temp_options_list)):
        options_dict[str(temp_options_list[i][0])] = {'rank': temp_options_list[i][3], 'cp_score': temp_options_list[i][1], 'mate_score': temp_options_list[i][2]}
    return options_dict


def get_move_quality(white_move, actual_cp_eval, actual_mate_eval, hyp_cp_eval, hyp_mate_eval):

    black_move = not white_move
    cp_merit = None 
    mate_merit = None

    if hyp_cp_eval is not None: 
        if actual_cp_eval is not None:
            cp_merit = (hyp_cp_eval - actual_cp_eval)
        else: 
            cp_merit = hyp_cp_eval
        if black_move:
            cp_merit = -1*cp_merit

    if actual_mate_eval is None and hyp_mate_eval is not None: # the mate evaluation just BEGUN, "B"
        if (white_move and hyp_mate_eval > 0) or (black_move and hyp_mate_eval < 0):
             mate_merit = "AB:" + str(abs(hyp_mate_eval))
        if (white_move and hyp_mate_eval < 0) or (black_move and hyp_mate_eval > 0):
             mate_merit = "DB:" + str(-abs(hyp_mate_eval))    

    elif actual_mate_eval is not None and hyp_mate_eval is not None: 
        if (actual_mate_eval >=0 and hyp_mate_eval >=0) or (actual_mate_eval <=0 and hyp_mate_eval <= 0): #the mate evaluation is a CONTINUATION from earlier game positions, "C"
            if (white_move and actual_mate_eval > 0) or (black_move and actual_mate_eval < 0):
                mate_merit = "AC:" + str(abs(hyp_mate_eval))
            if (white_move and actual_mate_eval < 0) or (black_move and actual_mate_eval > 0):
                mate_merit = "DC:" + str(-abs(hyp_mate_eval))
        else: #but if the mate value swiched signs, then a new mate line has just BEGUN, "B"
            if (white_move and hyp_mate_eval > 0) or (black_move and hyp_mate_eval < 0):
                mate_merit = "AB:" + str(abs(hyp_mate_eval))
            if (white_move and hyp_mate_eval < 0) or (black_move and hyp_mate_eval > 0):
                mate_merit = "DB:" + str(-abs(hyp_mate_eval))

    elif actual_mate_eval is not None and hyp_mate_eval is None: #the mate evaluation is LOST, "L"
        if (white_move and actual_mate_eval > 0) or (black_move and actual_mate_eval < 0):
            mate_merit = "AL:" + str(abs(actual_mate_eval))
        if (white_move and actual_mate_eval < 0) or (black_move and actual_mate_eval > 0):
             mate_merit = "DL:" + str(-abs(actual_mate_eval))

    #test; all signs point to these scenarios being impossible (as they probably should be)
    if hyp_cp_eval is not None and hyp_mate_eval is not None:
        if print_to_console:
            print("both cp and mate can not be none")
    if hyp_cp_eval is None and hyp_mate_eval is None:
        if print_to_console:
            print("they can both BE none....huh")
    return cp_merit, mate_merit


def rank_options(temp_options_list):
    
    attacks = []
    defenses = []
    cps = []
    for entry in temp_options_list:
        if entry[2] is not None: 
            if entry[2][0] == 'A' and entry[2][1] != 'L':
                attacks.append(entry)
            elif entry[2][0] == 'D' and entry[2][1] != 'L':
                defenses.append(entry)
            else: 
                cps.append(entry)
        else:
            cps.append(entry)
    attacks.sort(key=lambda x: int(x[2][3:]))
    defenses.sort(key=lambda x: int(x[2][3:]))
    if len(cps) > 1 and cps[0][1] is not None: #was getting the following error without this check: float() argument must be a string or a number, not 'NoneType'
        cps.sort(key=lambda x: -float(x[1]))

    num_cps = len(cps)
    num_attacks = len(attacks)

    attacks = append_rank_assignments(attacks, starting_rank = 1)
    cps = append_rank_assignments(cps, starting_rank=num_attacks+1)
    defenses = append_rank_assignments(defenses, starting_rank = (num_attacks+num_cps+1))
    temp_options_list = attacks + cps + defenses

    return temp_options_list

def append_rank_assignments(list_needing_rankings, starting_rank = 1):
    if len(list_needing_rankings) == 0:
        return []
    next_rank = starting_rank
    if list_needing_rankings[0][1] is None:
        for i in range(len(list_needing_rankings)):
            if len(list_needing_rankings[i]) > 3:
                next_rank += 1
                continue
            current_next_best = list_needing_rankings[i][2][3:]
            indices = [j for j, x in enumerate(list_needing_rankings) if x[2][3:] == current_next_best]
            for k in range(len(indices)):
                list_needing_rankings[indices[k]].append(next_rank)
            next_rank += 1
    else: 
        for i in range(len(list_needing_rankings)):
            if len(list_needing_rankings[i]) > 3:
                next_rank += 1
                continue
            current_next_best = list_needing_rankings[i][1]
            indices = [j for j, x in enumerate(list_needing_rankings) if x[1] == current_next_best]
            for k in range(len(indices)):
                list_needing_rankings[indices[k]].append(next_rank)
            next_rank += 1
    return list_needing_rankings


def initiate_engine_and_handler():
    cwd = os.getcwd()
    stockfish_path = os.path.join(cwd, "stockfish")
    engine = chess.uci.popen_engine(stockfish_path)
    engine.uci()
    engine.ucinewgame()
    handler = chess.uci.InfoHandler()
    engine.info_handlers.append(handler)
    return engine, handler


def add_relevant_game_details(game, perf):

    game_info_dict = game.headers

    if "WhiteElo" in game_info_dict:
        perf["elo_w"] = game_info_dict["WhiteElo"]
    else: 
        perf["elo_w"] = "?"
    
    if "BlackElo" in game_info_dict:
        perf["elo_b"] = game_info_dict["BlackElo"]
    else: 
        perf["elo_b"] = "?"

    if "White" in game_info_dict:
        perf["acc_name_w"] = game_info_dict["White"]
    else: 
        perf["acc_name_w"] = "?"

    if "Black" in game_info_dict:
        perf["acc_name_b"] = game_info_dict["Black"]
    else: 
        perf["acc_name_b"] = "?"

    if "Result" in game_info_dict:
        perf["result"] = game_info_dict["Result"]
    else: 
        perf["result"] = "?"

    if "WhiteRatingDiff" in game_info_dict:
        perf["rating_change_w"] = game_info_dict["WhiteRatingDiff"]
    else: 
        perf["rating_change_w"] = "?"

    if "BlackRatingDiff" in game_info_dict:
        perf["rating_change_b"] = game_info_dict["BlackRatingDiff"]
    else: 
        perf["rating_change_b"] = "?"

    if "UTCDate" in game_info_dict:
        perf["date"] = game_info_dict["UTCDate"]
    else: 
        perf["date"] = "?"

    if "UTCTime" in game_info_dict:
        perf["time"] = game_info_dict["UTCTime"]
    else: 
        perf["time"] = "?"

    if "ECO" in game_info_dict:
        perf["eco"] = game_info_dict["ECO"]
    else: 
        perf["eco"] = "?"

    if "Opening" in game_info_dict:
        perf["opening"] = game_info_dict["Opening"]
    else: 
        perf["opening"] = "?"

    if "Termination" in game_info_dict:
        perf["termination"] = game_info_dict["Termination"]
    else: 
        perf["termination"] = "?"

    if "TimeControl" in game_info_dict:
        perf["game_time_settings"] = game_info_dict["TimeControl"]
    else: 
        perf["game_time_settings"] = "?"

    perf["engine_eval_seconds"] = sec_eval_per_move

    if "Event" in game_info_dict:
        perf["event"] = game_info_dict["Event"]
    else: 
        perf["event"] = "?"

    if "Site" in game_info_dict:
        perf["site"] = game_info_dict["Site"]
    else: 
        perf["site"] = "?"

    #perf["elo_b"] = game.headers["BlackElo"]
    #perf["acc_name_w"] = game.headers["White"]
    #perf["acc_name_b"] = game.headers["Black"]
    #perf["result"] = game.headers["Result"]
    #perf["rating_change_w"] = game.headers["WhiteRatingDiff"]
    #perf["rating_change_b"] = game.headers["BlackRatingDiff"]
    #perf["date"] = game.headers["UTCDate"]
    #perf["time"] = game.headers["UTCTime"]
    #perf["eco"] = game.headers["ECO"]
    #perf["opening"] = game.headers["Opening"]
    #perf["termination"] = game.headers["Termination"]
    #perf["game_time_settings"] = game.headers["TimeControl"]    
    # perf["event"] = game.headers["Event"]
    # perf["site"] = game.headers["Site"]



    # wp["elo"] = game.headers["WhiteElo"]
    # wp["opp_elo"] = game.headers["BlackElo"]

    # wp["acc_name"] = game.headers["White"]
    # wp["opp_acc_name"] = game.headers["Black"]

    # bp["elo"] = game.headers["BlackElo"]
    # bp["opp_elo"] = game.headers["WhiteElo"]

    # bp["acc_name"] = game.headers["Black"]
    # bp["opp_acc_name"] = game.headers["White"]

    # wp['piece_color'] = "White"
    # bp['piece_color'] = "Black"
    
    # result = game.headers["Result"]
    # r1, r2 = interpret_result(result)
    
    # wp["result"] = r1
    # bp["result"] = r2

    # wp["rating_change"] = game.headers["WhiteRatingDiff"]
    # wp["opp_rating_change"] = game.headers["BlackRatingDiff"]

    # bp["rating_change"] = game.headers["BlackRatingDiff"]
    # bp["opp_rating_change"] = game.headers["WhiteRatingDiff"]


    # wp["date"] = game.headers["UTCDate"]
    # bp["date"] = game.headers["UTCDate"]   

    # wp["time"] = game.headers["UTCTime"]
    # bp["time"] = game.headers["UTCTime"] 

    # wp["eco"] = game.headers["ECO"]
    # bp["eco"] = game.headers["ECO"]

    # wp["opening"] = game.headers["Opening"]
    # bp["opening"] = game.headers["Opening"]

    # wp["termination"] = game.headers["Termination"]
    # bp["termination"] = game.headers["Termination"]

    # wp["game_time_settings"] = game.headers["TimeControl"]
    # bp["game_time_settings"] = game.headers["TimeControl"]

    # wp["engine_eval_seconds"] = sec_eval_per_move
    # bp["engine_eval_seconds"] = sec_eval_per_move

    # wp["event"] = game.headers["Event"]
    # bp["event"] = game.headers["Event"]
    
    # wp["site"] = game.headers["Site"]
    # bp["site"] = game.headers["Site"]

    return perf


def interpret_result(result):
    r1 = -1.0
    r2 = -1.0
    if len(result) == 3:
        r1 = float(result[0])
        r2 = float(result[2])
    if len(result) == 7:
        r1 = 0.5
        r2 = 0.5
    assert r1 != -1.0, "Bad result detected"
    assert r2 != -1.0, "Bad result detected"

    return r1, r2




def write_dict_to_csv(csv_file, csv_columns, dict):
    with open(csv_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writerow(dict)
    return 

def overwrite_skip_games_file(new_number):
    with open(skip_games_file, 'r+') as skipfile:
        data = skipfile.readline()
        skipfile.seek(0)
        skipfile.write(str(new_number))
        skipfile.truncate()
        if (print_to_console):
            print("Overwrote skip file to: ", str(new_number))
    return

def send_text_notification(message):
    t_cli.messages.create(body = message, from_ = t_num, to = my_p)


if __name__ == '__main__':
    main()
