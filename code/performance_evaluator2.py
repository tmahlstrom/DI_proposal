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
from multiprocessing import Pool
import sys
from twilio.rest import Client


skip_games = 0
batch_size = 1
num_batches = 50
sec_eval_per_move = 1
num_processors = 8
multiprocess_flag = False

sys.setrecursionlimit(10000)

text_notification_on = False
t_acc = 'AC4400f5964a54435cd2cba080478cb9c9'
t_tok = '96af49f32cd628d9aa50439b2d4ea944'
t_cli = Client(t_acc, t_tok)
t_num = '+17634029987'
my_p = '+16515874056'

writing_file = "/Users/tylerahlstrom/Documents/GitHub/DI_Proposal/data/stockfish_performances_fivesecondsxxxxyyyyy.csv"
csv_columns = ['elo','opp_elo', 'piece_color', 'opening', 'eco', 'result', 'engine_eval_time', 'game_type', 'termination', 'chosen_moves_eval', 'available_moves_eval', 'opp_chosen_moves_eval', 'opp_available_moves_eval']
pgns_all_path = "/Users/tylerahlstrom/Documents/GitHub/DI_Proposal/data/lichess_db_standard_rated_2017-03.pgn"
pgns = open(pgns_all_path)





def main():
    prepare_files()


    progress_count = 0
    for _ in range (num_batches):
        raw_games = []
        for _ in range(batch_size):
            pgn = chess.pgn.read_game(pgns)
            raw_games.append(pgn)
        multiprocess_batch(raw_games, multiprocess_flag)
        progress_count += batch_size * 2
        message = "Performances evaluated: " + str(progress_count)
        print(message)
        if (text_notification_on):
            send_text_notification(message)


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

    # wp_m = {}   #dictionary containing info about each move
    # bp_m = {}

    #score = 0   #move score, or more precisely, the stockfish evalation of the board after a move *minus* the evaluation before the move
    #initial_eval = 0
    cp_eval, mate_eval = get_abs_board_evaluation(engine, handler)

    # engine.go(movetime=sec_eval_per_move*1000)
    # board_eval = handler.info["score"][1].cp
    # best_option, _ = engine.go(movetime=sec_eval_per_move*1000)
    # score = handler.info["score"][1].cp

    for move in game.main_line():

        
        # move_options_dict = get_options_eval_dict(board, cp_eval, mate_eval, engine, handler)

        # chosen_move_info_dict = {'move': str(move), 'move_rank': move_options_dict[str(move)]['rank'], 'num_move_options': len(move_options_dict), 'move_cp_eval': move_options_dict[str(move)]['cp_score'], 'move_mate_eval': move_options_dict[str(move)]['mate_score']}
        # print("_", board.turn, chosen_move_info_dict['move_mate_eval'])

        # if board.turn == chess.WHITE:
        #     wp_available_moves.append(move_options_dict)
        #     wp_chosen_moves.append(chosen_move_info_dict)

        # elif board.turn == chess.BLACK:
        #     bp_available_moves.append(move_options_dict)
        #     bp_chosen_moves.append(chosen_move_info_dict)

        # cp_change = chosen_move_info_dict['move_cp_eval']
        # if cp_change is not None:
        #     if board.turn == chess.BLACK: 
        #         cp_change = -cp_change
        #     if cp_eval is not None:
        #         cp_eval += cp_change
        #     else:
        #         cp_eval = cp_change
        # else:
        #      cp_eval = None

        # mate_change = chosen_move_info_dict['move_mate_eval']
        # if mate_change is not None:
        #     mate_change = int(mate_change[3:])
        #     if board.turn == chess.BLACK: 
        #         mate_change = -mate_change
        #     if mate_eval is not None:
        #         mate_eval += mate_change
        #     else:
        #         mate_eval = mate_change
        # else:
        #      mate_eval = None
        engine.go(movetime=sec_eval_per_move*1000)
        new_cp_eval = handler.info["score"][1].cp
        new_mate_eval = handler.info["score"][1].mate
        print("*", new_cp_eval)
        print("*", new_mate_eval)
        board.push(move)
        engine.position(board)
        engine.go(movetime=sec_eval_per_move*1000)
        new_cp_eval = handler.info["score"][1].cp
        new_mate_eval = handler.info["score"][1].mate
        print(new_cp_eval)
        print(new_mate_eval)
            
        print("")
        print("")
        # cp_eval, mate_eval = get_board_evaluation(board, engine, handler)
        # print("*", board.turn, mate_eval)
        # engine.go(movetime=sec_eval_per_move*1000)
        # pre_move_board_eval = handler.info["score"][1].cp


    # print(wp_chosen_moves)
    # print(bp_chosen_moves)
    # wp["available_moves_eval"] = wp_available_moves
    # wp["chosen_moves_eval"] = wp_chosen_moves
    # wp["opp_available_moves_eval"] = bp_available_moves
    # wp["opp_chosen_moves_eval"] = bp_chosen_moves
    
    # bp["available_moves_eval"] = bp_available_moves
    # bp["chosen_moves_eval"] = bp_chosen_moves
    # bp["opp_available_moves_eval"] = wp_available_moves
    # bp["opp_chosen_moves_eval"] = wp_chosen_moves

    return wp, bp


def get_abs_board_evaluation(engine, handler, white_move = True):
    engine.go(movetime=sec_eval_per_move*1000)
    new_cp_eval = handler.info["score"][1].cp
    new_mate_eval = handler.info["score"][1].mate
    if not white_move:
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
        hyp_cp_eval, hyp_mate_eval = get_abs_board_evaluation(engine, handler, not board.turn) # not board.turn because it's not actually whose turn it is
        board.pop() #unmake the move
        engine.position(board)
        cp_merit, mate_merit = get_move_quality(board.turn, actual_cp_eval, actual_mate_eval, hyp_cp_eval, hyp_mate_eval)

        temp_options_list.append([move, cp_merit, mate_merit])
    temp_options_list.sort(key=lambda x: -float(x[1]))
    options_dict = {}
    for i in range (len(temp_options_list)):
        options_dict[str(temp_options_list[i][0])] = {'rank':i+1, 'cp_score': temp_options_list[i][1], 'mate_score': temp_options_list[i][2]}
    return options_dict


def get_move_quality(white_move, actual_cp_eval, actual_mate_eval, hyp_cp_eval, hyp_mate_eval):

    black_move = not white_move
    cp_merit = np.NaN
    mate_merit = None

    print(white_move, "hyp mate eval: ", hyp_mate_eval, "hyp cp eval: ", hyp_cp_eval)
    if actual_cp_eval is not None and hyp_cp_eval is not None:
        cp_merit = (hyp_cp_eval - actual_cp_eval)
        if black_move:
            cp_merit = -cp_merit

    if actual_mate_eval is None and hyp_mate_eval is not None: # the mate evaluation just BEGUN, "B"
        mate_merit = hyp_mate_eval
        if black_move:
            mate_merit = -mate_merit
        if (white_move and hyp_mate_eval > 0) or (black_move and hyp_mate_eval < 0):
             mate_merit = "AB:" + str(hyp_mate_eval)
        if (white_move and hyp_mate_eval < 0) or (black_move and hyp_mate_eval > 0):
             mate_merit = "DB:" + str(hyp_mate_eval)    

    if actual_mate_eval is not None and hyp_mate_eval is not None: 
        if (actual_mate_eval >=0 and hyp_mate_eval >=0) or (actual_mate_eval <=0 and hyp_mate_eval <= 0): #the mate evaluation is a CONTINUATION from earlier game positions, "C"
            mate_merit = (actual_mate_eval - hyp_mate_eval)
            if black_move:
                mate_merit = -mate_merit
            if (white_move and actual_mate_eval > 0) or (black_move and actual_mate_eval < 0):
                mate_merit = "AC:" + str(mate_merit)
            if (white_move and actual_mate_eval < 0) or (black_move and actual_mate_eval > 0):
                mate_merit = "DC:" + str(mate_merit)
        else: #but if the mate value swiched signs, then a new mate line has just BEGUN, "B"
            mate_merit = (hyp_mate_eval - actual_mate_eval) 
            if black_move:
                mate_merit = -mate_merit
            if (white_move and actual_mate_eval > 0) or (black_move and actual_mate_eval < 0):
                mate_merit = "AB:" + str(mate_merit)
            if (white_move and actual_mate_eval < 0) or (black_move and actual_mate_eval > 0):
                mate_merit = "DB:" + str(mate_merit)

    if actual_mate_eval is not None and hyp_mate_eval is None: #the mate evaluation is LOST, "L"
        if (white_move and actual_mate_eval > 0) or (black_move and actual_mate_eval < 0):
             mate_merit = "AL:" + str(abs(actual_mate_eval))
        if (white_move and actual_mate_eval < 0) or (black_move and actual_mate_eval > 0):
             mate_merit = "DL:" + str(abs(actual_mate_eval))

   

    #test
    if hyp_cp_eval is not None and hyp_mate_eval is not None:
        print("both cp and mate can not be none")
    if hyp_cp_eval is None and hyp_mate_eval is None:
        print("they can both BE none....huh")
    return cp_merit, mate_merit

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

    bp["elo"] = game.headers["BlackElo"]
    bp["opp_elo"] = game.headers["WhiteElo"]

    wp['piece_color'] = "White"
    bp['piece_color'] = "Black"
    
    result = game.headers["Result"]
    r1, r2 = interpret_result(result)
    
    wp["result"] = r1
    bp["result"] = r2

    wp["eco"] = game.headers["ECO"]
    bp["eco"] = game.headers["ECO"]

    wp["opening"] = game.headers["Opening"]
    bp["opening"] = game.headers["Opening"]

    wp["termination"] = game.headers["Termination"]
    bp["termination"] = game.headers["Termination"]

    wp["game_type"] = game.headers["TimeControl"]
    bp["game_type"] = game.headers["TimeControl"]

    wp["engine_eval_time"] = sec_eval_per_move
    bp["engine_eval_time"] = sec_eval_per_move

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
