import os.path
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def create_request_session(url):
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
        car_id = ad.get('data-id')
        if car_id:
            car_data[id_column_title] = car_id
        else:
            car_data[id_column_title] = 0
        car_listings.append(car_data)
    return car_listings

def get_total_pages_of_an_ad(soup):
    pagination = soup.find('ul', class_='pagination-list')
    if pagination:
        pages = pagination.find_all('li')
        return int(pages[-2].get_text().strip())  # Get the second last item as it contains the total pages
    return 1

def filter_and_sort_function(list_of_items):
    min_year = 2022
    min_price = 7000
    max_price = 10500
    max_km = 50000
    filtered_vehicles = [vehicle for vehicle in list_of_items if vehicle['Year'] >= min_year and min_price <= vehicle['Price'] <= max_price and vehicle['KM'] <= max_km]
    # Sort the filtered vehicles by year (ascending) and then by price (ascending)
    sorted_filtered_vehicles = sorted(filtered_vehicles, key=lambda x: (x['Year'], x['Price']))
    # for vehicle in sorted_filtered_vehicles:
    #     print(vehicle)
    print(f'{len(sorted_filtered_vehicles)} Vehicles found matching your filters !')
    return sorted_filtered_vehicles

def iterage_throug_ad_pages(web_site):
    print(f'Found a total number of {no_of_site_pages_with_ads} of autovit ads for {web_site}!')
    for page_num in range(1, no_of_site_pages_with_ads + 1):
        page_url = f"{web_site}?page={page_num}"
        print(f"Scraping page {page_num} of {web_site}")
        page_soup_session = create_request_session(page_url)
        car_listings = get_car_details(page_soup_session)
        all_car_listings.extend(car_listings)

def handle_excel_data_sheet(data, excel):
    if os.path.exists(excel):
        print("Excel file existing,reading now...")
        known_df = pd.read_excel(excel)
        new_df = pd.DataFrame(data)
        #compare if a new car posting exists or not
        if isinstance(new_df, pd.DataFrame) and not new_df.empty:
            known_df[id_column_title] = pd.to_numeric(known_df[id_column_title], errors='coerce').astype('Int64')
            known_cars = known_df[id_column_title].tolist()
            new_df[id_column_title] = pd.to_numeric(new_df[id_column_title], errors='coerce').astype('Int64')
            filtered_new_df = new_df[~new_df[id_column_title].isin(known_cars)]
            if not filtered_new_df.empty:
                print('New cars found !')
                updated_df = pd.concat([known_df, filtered_new_df], ignore_index=True)
                updated_df.to_excel(excel, index=False)
                new_cars_notif = dict(updated_df.iloc[:, :2].values)
                send_notification('New cars found :', new_cars_notif)
            else:
                print('No new item found !')
            # Check for price decreases
            merged_df = pd.merge(known_df, new_df, on=id_column_title, how='left', suffixes=('_old', '_new'))
            merged_df['Price_Decreased'] = merged_df['Price_new'] < merged_df['Price_old']
            # Filter rows where the price has decreased
            price_decreased_df = merged_df[merged_df['Price_Decreased'] == True]
            if not price_decreased_df.empty:
                print('Price decreases found:')
                # Optionally, update the known_df with the new (decreased) prices
                known_df.update(price_decreased_df[[id_column_title, 'Price_new']].rename(columns={'Price_new': 'Price'}))
                # Save the updated DataFrame back to Excel
                selected_columns =price_decreased_df[['Title_old','Price_old','Price_new','url_new']]
                price_change_notif = selected_columns.set_index('Title_old').T.to_dict('list')
                send_notification('Price change for :', price_change_notif)
                known_df.to_excel(excel, index=False)
            else:
                print('No price decreases found.')
        else :
            print("Empty DF !")
    else:
        print("Excel file not existing,creating now...")
        new_df = pd.DataFrame(data)
        new_cars_notif = dict(new_df.iloc[:, :2].values)
        new_df.to_excel(excel, index=False)
        send_notification('New cars found :', new_cars_notif)


def send_notification(notification,cars):
    token = "aqioije5jiex877tdp7fbbvhhd5eeh"
    user_key = "unjez5wivue53eb7ekfhyxrcxvavm6"

    url = "https://api.pushover.net/1/messages.json"
    message = (f"{notification}"
                f"Car links : {cars}")
    data = {
        "token": token,
        "user": user_key,
        "message": message
    }
    requests.post(url, data=data)


if __name__ == "__main__":
    while True:
        id_column_title = 'Unique_id'
        Excel_sheet_location = r'./Excel.xlsx'
        cars_to_find = ['/dacia/spring']
        autovit_site = ['https://www.autovit.ro/autoturisme' + item for item in cars_to_find]
        all_car_listings = []
        for web_site in autovit_site:
            request_session = create_request_session(web_site)
            no_of_site_pages_with_ads = get_total_pages_of_an_ad(request_session)
            iterage_throug_ad_pages(web_site)
        handle_excel_data_sheet(sorted_vehicles := filter_and_sort_function(all_car_listings), Excel_sheet_location)
        print('Waiting 2h till next iteration ...')
        time.sleep(10000)