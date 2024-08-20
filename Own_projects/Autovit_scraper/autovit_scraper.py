import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_url_info(url):
    html_text = requests.get(url)
    if html_text.status_code == 200:
        print(f"Success, responde code : {html_text.status_code}")
        # Step 3: Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_text.content, 'html.parser')
        return soup
    else:
        print(f'Error: {html_text.status_code}')
        return 0

def get_car_details(soup):
    car_listings = []
    soup_session = soup.find_all('article', class_='ooa-yca59n efpuxbr0')
    for ad in soup_session:
        car_data = {}
        # Extract the car name
        car_name = ad.find('h1',class_='efpuxbr9 ooa-1ed90th er34gjf0')
        car_data['Title'] = (car_name.get_text(strip=True))
        # Extract the URL
        link_tag = car_name.find('a') if car_name else None
        car_data['url'] = link_tag['href'] if link_tag else 'N/A'
        # Extract mileage
        mileage_tag = ad.find('dd', {'data-parameter': 'mileage'})
        if mileage_tag:
            mileage = mileage_tag.get_text(strip=True)
            mileage_cleaned = ''.join(filter(str.isdigit, mileage))
            car_data['KM'] = int(mileage_cleaned)
        else:
            car_data['KM'] = 'None'
        #Extract year
        year_tag = ad.find('dd', {'data-parameter': 'year'})
        if year_tag:
            year = int(year_tag.get_text(strip=True))
            car_data['Year'] = year
        else:
            car_data['Year'] = 0
        #Extract price
        price_tag = ad.find('h3',class_='efpuxbr16 ooa-1n2paoq er34gjf0')
        if price_tag:
            # Remove any non-numeric characters (like spaces, commas, or currency symbols)
            price_text = price_tag.get_text(strip=True)
            # Remove any non-numeric characters (like spaces, commas, or currency symbols)
            price_text_cleaned = ''.join(filter(str.isdigit, price_text)) #takes two arguments and return true of false '1' will be kepr, 'E'  will be removed
            car_data['Price'] = int(price_text_cleaned)
        else:
            car_data['Price'] = 0
        #Extract Fuel type
        fuel_tag = ad.find('dd', {'data-parameter': 'fuel_type'})
        if fuel_tag:
            fuel = fuel_tag.get_text(strip=True)
            car_data['Fuel'] = fuel
        else:
            car_data['Fuel'] = 'None'
        #Extract ad unique id
        unique_id = ad.get('data-id')
        if unique_id:
            car_data['Unique_id'] = unique_id
        else:
            car_data['Unique_id'] = 0
        car_listings.append(car_data)
    return car_listings

def get_total_pages(soup):
    pagination = soup.find('ul', class_='pagination-list')
    if pagination:
        pages = pagination.find_all('li')
        return int(pages[-2].get_text().strip())  # Get the second last item as it contains the total pages
    return 1

def sort_vehicles(list_of_items):
    min_year = 2019
    min_price = 18000
    max_price = 20000
    max_km = 100000
    filtered_vehicles = [vehicle for vehicle in list_of_items if vehicle['Year'] >= min_year and min_price <= vehicle['Price'] <= max_price and vehicle['KM'] <= max_km]
    # Sort the filtered vehicles by year (ascending) and then by price (ascending)
    sorted_filtered_vehicles = sorted(filtered_vehicles, key=lambda x: (x['Year'], x['Price']))
    # for vehicle in sorted_filtered_vehicles:
    #     print(vehicle)
    print(f'{len(sorted_filtered_vehicles)} Vehicles found matching your filters !')
    return sorted_filtered_vehicles

def iterage_throug_all_site_pages(web_site):
    print(f'Found a total number of {no_of_site_pages_with_ads} of autovit ads for {web_site}!')
    for page_num in range(1, no_of_site_pages_with_ads + 1):
        page_url = f"{web_site}?page={page_num}"
        print(f"Scraping page {page_num} of {web_site}")
        page_soup_session = get_url_info(page_url)
        car_listings = get_car_details(page_soup_session)
        all_car_listings.extend(car_listings)

def create_excel_file(data,excel):
    df = pd.DataFrame(data)
    df.to_excel(excel,index=False)


def send_notification(cars):
    token = "aqioije5jiex877tdp7fbbvhhd5eeh"
    user_key = "unjez5wivue53eb7ekfhyxrcxvavm6"

    url = "https://api.pushover.net/1/messages.json"
    car_urls = {}
    for item in cars:
        car_urls[item['Title']] = item['url']
    message = (f"Number of vehicles found: {len(sorted_vehicles)}\n"
                f"Car links : {car_urls}")
    data = {
        "token": token,
        "user": user_key,
        "message": message
    }

    requests.post(url, data=data)

def get_car_id(excel):
    data = pd.read_excel(excel)
    df = data['Unique_id']
    if not df.empty:
        return list(df)
    else:
        return 0

if __name__ == "__main__":
    excel_file = r'E:\GIT_HUB\automotive_repo\Own_projects\Autovit_scraper\Excel.xlsx'
    cars_to_find = ['/skoda/superb','/volkswagen/passat']
    base_url = 'https://www.autovit.ro/autoturisme'
    autovit_site = [base_url + item for item in cars_to_find]
    all_car_listings = []
    for web_site in autovit_site:
        request_session = get_url_info(web_site)
        no_of_site_pages_with_ads = get_total_pages(request_session)
        iterage_throug_all_site_pages(web_site)
    create_excel_file(sorted_vehicles := sort_vehicles(all_car_listings), excel_file)
    known_vehicles = get_car_id(excel_file)
    send_notification(sorted_vehicles)


