import requests
from bs4 import BeautifulSoup

autovit_site = 'https://www.autovit.ro/autoturisme/volkswagen/passat'

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
    soup_session = soup.find_all('section', class_='ooa-qat6iw efpuxbr1')
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
            car_data['KM'] = mileage
        else:
            car_data['KM'] = 'None'
        #Extract year
        year_tag = ad.find('dd', {'data-parameter': 'year'})
        if year_tag:
            year = year_tag.get_text(strip=True)
            car_data['Year'] = year
        else:
            car_data['Year'] = 'None'
        #Extract price
        price_tag = ad.find('h3',class_='efpuxbr16 ooa-1n2paoq er34gjf0')
        if price_tag:
            car_data['Price'] = price_tag.get_text(strip=True)
        else:
            car_data['Price'] = 'None'

        car_listings.append(car_data)
        #Extract Fuel type
        fuel_tag = ad.find('dd', {'data-parameter': 'fuel_type'})
        if fuel_tag:
            fuel = fuel_tag.get_text(strip=True)
            car_data['Fuel'] = fuel
        else:
            car_data['Fuel'] = 'None'

    for item in car_listings:
        print(item['Price'])
    return car_listings

def get_total_pages(soup):
    pagination = soup.find('ul', class_='pagination-list')
    if pagination:
        pages = pagination.find_all('li')
        return int(pages[-2].get_text().strip())  # Get the second last item as it contains the total pages
    return 1


if __name__ == "__main__":
    soup_info = get_url_info(autovit_site)
    total_pages = get_total_pages(soup_info)
    get_car_details(soup_info)
