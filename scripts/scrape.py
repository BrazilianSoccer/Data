from multiprocessing import Process
from copy import deepcopy
from functions import *
from glob import glob
import requests
import json
import csv
import os

from PyPDF2 import *

def make_directories(competitions, min_year, max_year):
    '''
    Creates directories for storing PDF and CSV files for each competition and year.
    
    Args:
        competitions (list): A list of competition names, codes and number of games in the format [(name, code, n_games)].
        min_year (int): The minimum year.
        max_year (int): The maximum year.
    '''

    for competition in competitions:
        name = competition[0]
        if name not in os.listdir(): os.mkdir(name)
        os.chdir(name)
        for year in range(min_year, max_year + 1):
            year = str(year)
            if year not in os.listdir(): os.mkdir(year)
            os.chdir(year)
            if 'PDFs' not in os.listdir(): os.mkdir('PDFs')
            if 'CSVs' not in os.listdir(): os.mkdir('CSVs')
            os.chdir('..')
        
        os.chdir('..')

def extract_games(competition, cod, year, n_max, files):
    '''
    Extracts games data from PDF files and saves them as PDF and CSV files.
    
    Args:
        competition (str): The name of the competition.
        cod (str): The code of the competition.
        year (int): The year of the games.
        n_max (int): The maximum number of games.
        files (list): A list of existing file paths.
    '''

    count_end = 0
    for game in range(1, n_max + 1):
        if count_end == 10: break
        try:
            name = f'../results/{competition}/{year}/PDFs/{str(game).zfill(3)}.pdf'
            if name.replace('PDFs', 'CSVs').replace('pdf', 'csv') in files:
                count_end = 0
                continue
            
            pdf = get_pdf(f'https://conteudo.cbf.com.br/sumulas/{year}/{cod}{game}se.pdf')
            if b'File or directory not found' in pdf:
                count_end += 1
                continue
            
            with open(name, 'wb') as f:
                f.write(pdf)
                count_end = 0
                
            reader = PdfReader(name)
            doc = []
            for i in range(len(reader.pages)):
                page = reader.pages[i]
                doc += page.extract_text().split('\n')
                
            for i in range(len(doc)): doc[i] = [doc[i]]
            name = name.replace('PDFs', 'CSVs')
            name = name.replace('pdf', 'csv')
            with open(name, 'w') as f:
                write = csv.writer(f)
                write.writerows(doc)
                
        except: pass

def get_pdf(url):
    '''
    Retrieves the content of a PDF file from the specified URL.
    
    Args:
        url (str): The URL of the PDF file.
    
    Returns:
        bytes: The content of the PDF file.
    '''

    return requests.get(url).content

def scrape(competitions, min_year, max_year, files, max_time = 600, cleaning = True):
    '''
    Scrapes games data from websites and saves them as PDF and CSV files.
    
    Args:
        competitions (list): A list of competition names, codes and number of games in the format [(name, code, n_games)].
        min_year (int): The minimum year.
        max_year (int): The maximum year.
        files (list): A list of existing file paths.
        max_time (int): The maximum time (in seconds) to wait for each scraping process. Defaults to 600 seconds.
        cleaning (bool): Flag indicating whether to clear the console output before scraping. Defaults to True.
    '''

    errors = {}
    for competition in competitions:
        competition, cod, n_games = competition
        errors[competition] = {}
        for year in range(min_year, max_year + 1):
            if cleaning: clear()
            print(f'Beggining scrape of {competition.replace("_", " ")} {year}')
            year = str(year)
            errors[competition][year] = []
            p = Process(target = extract_games, args = (competition, cod, year, n_games, files))
            p.start()
            p.join(max_time)
            p.terminate()

def extract(competitions, min_year, max_year, cleaning = True):
    '''
    Extracts game data from CSV files and generates summary files for each competition and year.
    
    Args:
        competitions (list): A list of competition names, codes and number of games in the format [(name, code, n_games)].
        min_year (int): The minimum year.
        max_year (int): The maximum year.
        cleaning (bool): Flag indicating whether to clear the console output before extracting. Defaults to True.
    
    Returns:
        int: The total number of extraction failures.
    '''

    with open('../auxiliary/exceptions.json', 'r') as f: exceptions = json.load(f)

    errors = {}
    cont_fail = 0
    for competition in competitions:
        competition, n_games = competition[0], competition[2]
        for year in range(min_year, max_year + 1):
            if cleaning: clear()
            year = str(year)
            print(f'Beggining extract of {competition.replace("_", " ")} {year}')
            games = {}
            count_end = 0
            if f'games.json' in os.listdir(f'../results/{competition}/{year}'):
                files = glob(f'../results/{competition}/{year}/CSVs/*.csv')
                latest_file = max(files, key = os.path.getmtime)
                mod_time = os.path.getmtime(latest_file)
                if mod_time < os.path.getmtime(f'../results/{competition}/{year}/games.json'): continue
            
            summary = [['Game', 'Home', 'Away']]
            for game in range(1, n_games + 1):
                if str(game).zfill(3) in exceptions[competition][year]:
                    if exceptions[competition][year][str(game).zfill(3)] != {}:
                        games[str(game).zfill(3)] = exceptions[competition][year][str(game).zfill(3)]
                        summary.append([str(game).zfill(3), games[str(game).zfill(3)]['Home'], games[str(game).zfill(3)]['Away']])
                        
                    continue
                
                if count_end == 10: break
                f_club, f_result, f_players, f_goals, f_changes = False, False, False, False, False
                try:
                    with open(f'../results/{competition}/{year}/CSVs/{str(game).zfill(3)}.csv', 'r') as f: text = ''.join(f.readlines())

                    clubs = catch_teams(text)
                    assert len(clubs) == 1
                    f_club = True
                
                    result = final_result(text)
                    assert len(result) == 1
                    result = result[0]
                    f_result = True
                
                    players = catch_players(text)
                    assert len(players) >= 28
                    f_players = True
                
                    goals = catch_goals(text)
                    aux = result.upper().split('X')
                    assert len(goals) == int(aux[0].strip()) + int(aux[-1].strip())
                    f_goals = True
                
                    changes = find_changes(text)
                    assert len(changes) <= 10
                    f_changes = True

                    yellow_cards = catch_yellow_cards(text)
                    red_cards = catch_red_cards(text)
                
                    games[str(game).zfill(3)] = {'Home'         : clubs[0][0],
                                                 'Away'         : clubs[0][1],
                                                 'Result'       : result,
                                                 'Players'      : players,
                                                 'Goals'        : goals,
                                                 'Changes'      : changes,
                                                 'Yellow cards' : yellow_cards,
                                                 'Red cards'    : red_cards}

                    count_end = 0
                    summary.append([str(game).zfill(3), clubs[0][0], clubs[0][1]])
                    
                except FileNotFoundError: count_end += 1
                except AssertionError:
                    cont_fail += 1
                    if not f_club: erro = 'Club'
                    elif not f_result: erro = 'Result'
                    elif not f_players: erro = 'Players'
                    elif not f_goals: erro = 'Goals'
                    elif not f_changes: erro = 'Changes'
                    else: erro = 'Not found'
                    
                    if competition in errors:
                        if year in errors[competition]:
                            errors[competition][year][str(game).zfill(3)] = erro
                        else:
                            errors[competition][year] = {}
                            errors[competition][year][str(game).zfill(3)] = erro
                    else:
                        errors[competition] = {}
                        errors[competition][year] = {}
                        errors[competition][year][str(game).zfill(3)] = erro

            with open(f'../results/{competition}/{year}/games.json', 'w') as f: json.dump(games, f)
            with open(f'../results/{competition}/{year}/summary.csv', 'w') as f:
                writer = csv.writer(f)
                for row in summary: writer.writerow(row)
                    
    with open('../results/infos_errors.json', 'w') as f: json.dump(errors, f)
    return cont_fail

def catch_squads(competitions, min_year, max_year, cleaning = True):
    '''
    Updates the lineups data for each game in the specified competitions and years.
    
    Args:
        competitions (list): A list of competition names, codes and number of games in the format [(name, code, n_games)].
        min_year (int): The minimum year.
        max_year (int): The maximum year.
        cleaning (bool): Flag indicating whether to clear the console output before updating lineups. Defaults to True.
    '''

    model = {'Home' : [],
             'Away' : [],
             'Time' : 0,
             'Score' : [0, 0]}

    for competition in competitions:
        competition = competition[0]
        for year in range(min_year, max_year + 1):
            year = str(year)
            if cleaning: clear()
            print(f'Beggining lineups update of {competition.replace("_", " ")} {year}')
            if f'squads.json' in os.listdir(f'{competition}/{year}'):
                files = glob(f'../results/{competition}/{year}/CSVs/*.csv')
                latest_file = max(files, key = os.path.getmtime)
                mod_time = os.path.getmtime(latest_file)
                if mod_time < os.path.getmtime(f'../results/{competition}/{year}/squads.json'): continue

            squads = {}
            with open(f'../results/{competition}/{year}/games.json') as f: games = json.load(f)
            
            for game in games:
                if games[game] == {}: continue

                home = games[game]['Home']
                away = games[game]['Away']
                players = games[game]['Players']
                if players[0][1] == players[-1][1]: continue
                
                game_players = treat_game_players(players, home, away)
                changes = treat_game_changes(games[game]['Changes'], home, away)
                goals = treat_game_events(games[game]['Goals'], home, away)
                red_cards = treat_game_events(games[game]['Red cards'], home, away)
                yellow_cards = treat_game_events(games[game]['Yellow cards'], home, away)
                if len(red_cards) > 0:
                    for i, red_card in enumerate(red_cards):
                        red_card = list(red_card)
                        club = red_card.pop()
                        red_card.insert(0, club)
                        red_card.insert(2, '')
                        red_cards[i] = tuple(red_card)

                changes += red_cards
                changes = sorted(changes, key = lambda x : x[1])
                squads[game] = {}
                squads[game][0] = deepcopy(model)
                for player in players:
                    if player[1] == home: game_club = 'Home'
                    else: game_club = 'Away'
                    if len(squads[game][0][game_club]) == 11: continue
                    cod = re.findall('\d{6}', player[0])[0]
                    squads[game][0][game_club].append(cod)
                    
                actual_minute = 0
                changes_breaks = 0
                for i, change in enumerate(changes):
                    old_home = deepcopy(squads[game][changes_breaks]['Home'])
                    old_away = deepcopy(squads[game][changes_breaks]['Away'])
                    
                    club, time, player_in, player_out = change
                    player_in = game_players[club][player_in] if player_in != '' else ''
                    player_out = game_players[club][player_out]
                    if time != actual_minute:
                        changes_breaks += 1
                        squads[game][changes_breaks] = deepcopy(squads[game][changes_breaks - 1])
                        if club == home:
                            if player_in != '':
                                old_home.remove(player_out)
                                old_home.append(player_in)
                            elif player_out in old_home:
                                old_home.remove(player_out)
                        else:
                            if player_in != '':
                                old_away.remove(player_out)
                                old_away.append(player_in)
                            elif player_out in old_away:
                                old_away.remove(player_out)
                        
                        squads[game][changes_breaks]['Home'] = deepcopy(old_home)
                        squads[game][changes_breaks]['Away'] = deepcopy(old_away)
                        squads[game][changes_breaks - 1]['Time'] = time - actual_minute
                        for goal in goals:
                            minute, player, team = goal
                            if minute > actual_minute and minute <= time:
                                if team == home: squads[game][changes_breaks - 1]['Score'][0] += 1
                                else: squads[game][changes_breaks - 1]['Score'][1] += 1
                                
                        if i == len(changes) - 1:
                            squads[game][changes_breaks]['Time'] = 90 - time
                            for goal in goals:
                                minute, player, team = goal
                                if minute > time:
                                    if team == home: squads[game][changes_breaks]['Score'][0] += 1
                                    else: squads[game][changes_breaks]['Score'][1] += 1
                    
                    else:
                        if club == home:
                            if player_in != '':
                                old_home.remove(player_out)
                                old_home.append(player_in)
                            elif player_out in old_home:
                                old_home.remove(player_out)
                        else:
                            if player_in != '':
                                old_away.remove(player_out)
                                old_away.append(player_in)
                            elif player_out in old_away:
                                old_away.remove(player_out)
                        
                        squads[game][changes_breaks]['Home'] = deepcopy(old_home)
                        squads[game][changes_breaks]['Away'] = deepcopy(old_away)
                        if i == len(changes) - 1: squads[game][changes_breaks]['Time'] = 90 - time
                            
                    actual_minute = time
            
            with open(f'../results/{competition}/{year}/squads.json', 'w') as f: json.dump(squads, f)
