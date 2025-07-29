import requests
from bs4 import BeautifulSoup
from itertools import combinations
from collections import Counter
from datetime import datetime
from datetime import date

def create_request_session(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    html_text = requests.get(url, headers=headers)
    if html_text.status_code == 200:
        print(f"Success, responde code : {html_text.status_code}")
        # Step 3: Parse the HTML content using BeautifulSoup
        request_session = BeautifulSoup(html_text.content, 'html.parser')
        return request_session
    else:
        print(f'Error: {html_text.status_code}')
        return 0

def get_loto_numbers(soup):
    year_dict = {'ianuarie': '', 'februarie': '', 'martie': '', 'aprilie': '','mai':'','iunie':'', 'iulie': '', 'august': '',
                 'septembrie': '', 'octombrie': '', 'noiembrie': '', 'decembrie': ''}
    date_cells = soup.find_all('td', class_=['odd','even'], nowrap=True)
    year_dict = {key: [] for key in year_dict.keys()}
    for item in date_cells:
        for key in year_dict.keys():
            if key in item.text:
                sibling = item.find_next_sibling()
                while sibling and sibling.get('class') in [['odd_rounded'], ['even_rounded']]:
                    year_dict[key].append(sibling.text)
                    sibling = sibling.find_next_sibling()
    for month in year_dict.keys():
        year_dict[month] = split_into_group_of_no(year_dict[month])
    return year_dict

def send_notification(message):
    token = "aqioije5jiex877tdp7fbbvhhd5eeh"
    user_key = "unjez5wivue53eb7ekfhyxrcxvavm6"

    url = "https://api.pushover.net/1/messages.json"
    message = f"Loto: {message}"
    data = {
        "token": token,
        "user": user_key,
        "message": message
    }
    requests.post(url, data=data)

def get_day_of_week():
    today = date.today().weekday()
    now = int(datetime.now().strftime('%H'))
    if (today == 2 or today == 5) and now >= 18:
        return True
    else:
        return False

def split_into_group_of_no(list_of_no:list):
    batch_size = 6
    return [list_of_no[i:i+batch_size] for i in range(0, len(list_of_no), batch_size)]

def check_missing_numbers(dictionary:dict,months):
    all_numbers = [x for x in range(1, 50)]
    missing_numbers = set()
    extracted_numbers = []
    for month in months:
        flattened_list = [int(num) for batch in dictionary[month] for num in batch]
        extracted_numbers.extend(flattened_list)
    for element_to_find in all_numbers:
        if element_to_find not in extracted_numbers:
            missing_numbers.add(element_to_find)
    print(f'In months {[x for x in months]},following numbers were NOT extracted: {[y for y in missing_numbers]}')
    return missing_numbers

def check_most_common_numbers(lotto_number_dict):
    all_values = []
    for value in lotto_number_dict.values():
        for sublist in value:
            if isinstance(sublist,list):
                all_values.extend(sublist)
            else:
                print("Unexpected Data Format:", sublist)
    all_values = [int(item) for item in all_values]
    counter = Counter(all_values)
    print(f"Most common used numbers: {counter.most_common(6)}")
    print(f"Least common used numbers: {counter.most_common()[:-10:-1]}")
    return counter.most_common(6),counter.most_common()[:-10:-1]

def current_month():
    romanian_months = {
    1: "Ianuarie",
    2: "Februarie",
    3: "Martie",
    4: "Aprilie",
    5: "Mai",
    6: "Iunie",
    7: "Iulie",
    8: "August",
    9: "Septembrie",
    10: "Octombrie",
    11: "Noiembrie",
    12: "Decembrie"}
    current_month = datetime.now().month
    previous = current_month -1
    before_previous_month = current_month - 2 if current_month > 1 else 12
    current_month_name = romanian_months[previous].lower()
    previous_month_name = romanian_months[before_previous_month].lower()
    return [previous_month_name,current_month_name]

def merge_dictionraies_lists(*dicts):
    merged_data = {}
    for data in dicts:
        for month, draws in data.items():
            merged_data.setdefault(month, []).extend(draws)
    return merged_data

def check_combinations(*lists,dataset:dict):
    uncommon = []
    full_combo = []
    intersection_numbers = []
    for item in lists:
        for subitem in item:
            if isinstance(subitem,tuple):
                uncommon.append(subitem[0])
            if isinstance(subitem,int):
                uncommon.append(subitem)
    for month, draws_list in dataset.items():
        for draw in draws_list:
            draw_numbers = set(map(int,draw))
            for combo in combinations(uncommon, 6):
                combo = set(map(int,combo))
                if combo.issubset(draw_numbers):
                    full_combo.append(combo)
                common_elements = combo.intersection(draw_numbers)
                if len(common_elements) >= 3:
                                intersection_numbers.append(common_elements)
                                # print(f"Found common elements: {common_elements} in combo {combo} and draw {draw_numbers}")
    unique_sets = set(map(frozenset, intersection_numbers))
    partial_combo = [set(item) for item in unique_sets]
    return partial_combo,full_combo

if __name__ == '__main__':
    url = 'http://noroc-chior.ro/Loto/6-din-49/arhiva-rezultate.php?Y=2025'
    url_2024 = 'http://noroc-chior.ro/Loto/6-din-49/arhiva-rezultate.php?Y=2024'
    soup = create_request_session(url)
    soup_2024 = create_request_session(url_2024)
    lotto_number_dict = get_loto_numbers(soup)
    lotto_number_dict_2024 = get_loto_numbers(soup_2024)
    months = current_month()
    missing_numbers = check_missing_numbers(lotto_number_dict,current_month())
    most_common,less_common = check_most_common_numbers(lotto_number_dict)
    merged_dictionaries = merge_dictionraies_lists(lotto_number_dict,lotto_number_dict_2024)
    combinatii_partiale, combinatii_totale = (check_combinations(missing_numbers,less_common,dataset=merged_dictionaries))
    message = (f"In months {list(months)}, following numbers were NOT extracted: {list(missing_numbers)}\n"
           f"Most common used numbers: {most_common}\n"
           f"Least common used numbers: {less_common}\n"
           f"Full combo: {combinatii_totale}")
    partial_combos = f"Partial combo: {combinatii_partiale}"
    send_notification(message)
    send_notification(partial_combos)

    '''Cele mai extrase, nu se mai pun ,ex 23 nu se pune '''
    all_numbers = Counter()
    historical_draws = []
    for items,values in lotto_number_dict.items():
        for item in values:
            all_numbers.update(item)
            historical_draws.append(item)
    top_16 = [num for num, _ in all_numbers.most_common(16)]
    top_16_set = set(top_16)

    def covered(draw, base_set, threshold=3):
        return len(set(draw) & base_set) >= threshold
    #
    coverage_count = sum(covered(draw, top_16_set) for draw in historical_draws)
    send_notification(f"Top 16 Numbers: {sorted(top_16)}")
    print(f"Draws Covered (3 matches): {coverage_count} out of {len(historical_draws)}")
