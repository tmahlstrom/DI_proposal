import chess
import chess.uci
import chess.pgn
import os
import csv
import matplotlib.pyplot as plt
from numpy import array
import numpy as np
import math
import time
from datetime import datetime
from multiprocessing import Pool
import sys
from twilio.rest import Client


skip_games = 455
batch_size = 25
num_batches = 4
sec_eval_per_move = 1.0
num_processors = 8
multiprocess_flag = True

sys.setrecursionlimit(10000)

text_notification_on = False
t_acc = 'AC4400f5964a54435cd2cba080478cb9c9'
t_tok = '96af49f32cd628d9aa50439b2d4ea944'
t_cli = Client(t_acc, t_tok)
t_num = '+17634029987'
my_p = '+16515874056'

writing_file = "/Users/tylerahlstrom/Documents/GitHub/DI_Proposal/data/stockfish_performances_1sec.csv"
csv_columns = ['elo', 'acc_name', 'opp_elo', 'opp_acc_name', 'date', 'time', 'piece_color', 'opening', 'eco', 'result', 'rating_change', 'opp_rating_change', 'event', 'engine_eval_seconds', 'game_type', 'termination', 'chosen_moves_eval', 'available_moves_eval', 'opp_chosen_moves_eval', 'opp_available_moves_eval', 'site']
pgns_all_path = "/Users/tylerahlstrom/Documents/GitHub/DI_Proposal/data/lichess_db_standard_rated_2017-03.pgn"
pgns = open(pgns_all_path)





def main():
    start_time = datetime.now()
    prepare_files()
    print("starting at game: ", skip_games + 1)
    progress_count = 0

    for _ in range (num_batches):
        raw_games = []
        for _ in range(batch_size):
            pgn = chess.pgn.read_game(pgns)
            raw_games.append(pgn)
        multiprocess_batch(raw_games, multiprocess_flag)
        progress_count += batch_size
        message = "Games evaluated: " + str(progress_count)
        print(message)
        if (text_notification_on):
            send_text_notification(message)
    
    end_time = datetime.now()
    print("Process duration: ", (end_time - start_time))


def prepare_files():
    with open(writing_file, 'a') as csvfile:
        if os.stat(writing_file).st_size == 0:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
    if skip_games > 0:
        skip_to_game(pgns, skip_games)


def multiprocess_batch(raw_games, multiprocess = True):
    if multiprocess:
        pool = Pool(num_processors)
        pool.map(evaluate_game,raw_games)
        pool.close()
        pool.join()
    else:
        for game in raw_games:
            evaluate_game(game)


def evaluate_game(game):
    performances = get_performance_dicts(game)
    for performance_dict in performances:
        write_dict_to_csv(writing_file, csv_columns, performance_dict)


def get_performance_dicts(game): 

    engine, handler = initiate_engine_and_handler()
    board = game.board()
    engine.position(board)

    wp = {}     #white perforamnce
    bp = {}     #black performance
    wp, bp = add_relevant_game_details(game, wp, bp)

    wp_available_moves = []   #list of dictionaries containing info about each avaiable move at each (ordered) turn
    bp_available_moves = []

    wp_chosen_moves = []   #list of dictionaries containing info about each (ordered) chosen move
    bp_chosen_moves = []

    cp_eval, mate_eval = get_abs_board_evaluation(engine, handler, board)

    for move in game.main_line():

        
        move_options_dict = get_options_eval_dict(board, cp_eval, mate_eval, engine, handler)

        chosen_move_info_dict = {'move': str(move), 'move_rank': move_options_dict[str(move)]['rank'], 'num_move_options': len(move_options_dict), 'move_cp_merit': move_options_dict[str(move)]['cp_score'], 'move_mate_merit': move_options_dict[str(move)]['mate_score']}

        if board.turn == chess.WHITE:
            wp_available_moves.append(move_options_dict)
            wp_chosen_moves.append(chosen_move_info_dict)

        elif board.turn == chess.BLACK:
            bp_available_moves.append(move_options_dict)
            bp_chosen_moves.append(chosen_move_info_dict)

        cp_change = chosen_move_info_dict['move_cp_merit']
        if cp_change is not None:
            if board.turn == chess.BLACK: 
                cp_change = -cp_change
            if cp_eval is not None:
                cp_eval += cp_change
            else:
                cp_eval = cp_change
        else:
             cp_eval = None

        mate_change = chosen_move_info_dict['move_mate_merit']
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

    wp["available_moves_eval"] = wp_available_moves
    wp["chosen_moves_eval"] = wp_chosen_moves
    wp["opp_available_moves_eval"] = bp_available_moves
    wp["opp_chosen_moves_eval"] = bp_chosen_moves
    
    bp["available_moves_eval"] = bp_available_moves
    bp["chosen_moves_eval"] = bp_chosen_moves
    bp["opp_available_moves_eval"] = wp_available_moves
    bp["opp_chosen_moves_eval"] = wp_chosen_moves

    return wp, bp


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
        print("both cp and mate can not be none")
    if hyp_cp_eval is None and hyp_mate_eval is None:
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
    engine = chess.uci.popen_engine("/Applications/Stockfish/src/stockfish")
    engine.uci()
    engine.ucinewgame()
    handler = chess.uci.InfoHandler()
    engine.info_handlers.append(handler)
    return engine, handler


def add_relevant_game_details(game, wp, bp):

    wp["elo"] = game.headers["WhiteElo"]
    wp["opp_elo"] = game.headers["BlackElo"]

    wp["acc_name"] = game.headers["White"]
    wp["opp_acc_name"] = game.headers["Black"]

    bp["elo"] = game.headers["BlackElo"]
    bp["opp_elo"] = game.headers["WhiteElo"]

    bp["acc_name"] = game.headers["Black"]
    bp["opp_acc_name"] = game.headers["White"]

    wp['piece_color'] = "White"
    bp['piece_color'] = "Black"
    
    result = game.headers["Result"]
    r1, r2 = interpret_result(result)
    
    wp["result"] = r1
    bp["result"] = r2

    wp["rating_change"] = game.headers["WhiteRatingDiff"]
    wp["opp_rating_change"] = game.headers["BlackRatingDiff"]

    bp["rating_change"] = game.headers["BlackRatingDiff"]
    bp["opp_rating_change"] = game.headers["WhiteRatingDiff"]


    wp["date"] = game.headers["UTCDate"]
    bp["date"] = game.headers["UTCDate"]   

    wp["time"] = game.headers["UTCTime"]
    bp["time"] = game.headers["UTCTime"] 

    wp["eco"] = game.headers["ECO"]
    bp["eco"] = game.headers["ECO"]

    wp["opening"] = game.headers["Opening"]
    bp["opening"] = game.headers["Opening"]

    wp["termination"] = game.headers["Termination"]
    bp["termination"] = game.headers["Termination"]

    wp["game_type"] = game.headers["TimeControl"]
    bp["game_type"] = game.headers["TimeControl"]

    wp["engine_eval_seconds"] = sec_eval_per_move
    bp["engine_eval_seconds"] = sec_eval_per_move

    wp["event"] = game.headers["Event"]
    bp["event"] = game.headers["Event"]
    
    wp["site"] = game.headers["Site"]
    bp["site"] = game.headers["Site"]

    return wp, bp


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


def skip_to_game(pgn_file, num_to_skip):

    offsets = chess.pgn.scan_offsets(pgn_file)
    book_mark = next(offsets)
    for i in range(num_to_skip):
        book_mark = next(offsets)
        if i == (num_to_skip - 1):
            pgn_file.seek(book_mark)


def write_dict_to_csv(csv_file, csv_columns, dict):
    with open(csv_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writerow(dict)
    return 


def send_text_notification(message):
    t_cli.messages.create(body = message, from_ = t_num, to = my_p)


if __name__ == '__main__':
    main()
