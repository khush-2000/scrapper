from bs4 import BeautifulSoup
import csv
import requests
import pandas as pd

symb = input("Enter company Symbol: ")

def p_n_l(symb):
    # URL of the website
    url = "https://www.screener.in/company/" + symb + "/consolidated/"

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code != 200:
        return f"Error: Unable to fetch data for symbol {symb}. Please check the symbol and try again."

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the 'Profit & Loss' section
    profit_loss_section = soup.find('section', {'id': 'profit-loss'})

    # Check if the 'Profit & Loss' section is found
    if profit_loss_section:
        # Find the 'Profit & Loss' table containing the required data
        profit_loss_table = profit_loss_section.find('table', class_='data-table')

        # Check if the table is found
        if profit_loss_table:
            # Extract the header row
            header_row = profit_loss_table.find('thead').find('tr')

            # Extract the column headers
            columns = [th.text.strip() for th in header_row.find_all('th')[1:]]

            # Rows to extract
            rows_to_extract = ['Sales', 'Interest', 'Depreciation', 'Profit before tax']

            # Extract the data rows
            data_rows = profit_loss_table.find('tbody').find_all('tr')

            # Create an empty list to store the data
            data_list = []

            # Iterate through each data row and extract the values for the specified rows
            for row in data_rows:
                # Extract the row header (e.g., Sales, Interest, etc.) and replace non-alphanumeric characters
                row_header = ''.join(filter(str.isalnum, row.find('td', class_='text').text.strip()))

                # Check if the current row is in the specified rows to extract
                if row_header in rows_to_extract:
                    # Extract the row values and add to the list as a tuple
                    values = [td.text.strip() for td in row.find_all('td')[1:]]
                    data_list.append((row_header, *values))

            # Check if 'Profit before tax' is not found and add it manually
            if 'Profit before tax' not in [row[0] for row in data_list]:
                profit_before_tax_row = profit_loss_table.find('tr', {'class': 'strong'})
                values = [td.text.strip() for td in profit_before_tax_row.find_all('td')[1:]]
                data_list.append(('Profit before tax', *values))

            # Create a dataframe from the list of tuples
            df = pd.DataFrame(data_list, columns=['Row Header'] + columns)

            # Transpose the dataframe
            df_res = df.set_index('Row Header').transpose()
            
            # removing commas
            df_res = df_res.applymap(lambda x: x.replace(',', ''))

            # converting objects into ints
            df_res = df_res.astype(int)

            # calculating EBITDA and removing Interest, Depreciation column and PBT column
            df_res['EBITDA'] = df_res['Interest'] + df_res['Depreciation'] + df_res['Profit before tax']
            df_res.drop(columns=['Interest', 'Depreciation', 'Profit before tax'], inplace=True)

            # calculating EBITDA growth
            df_res['EBITDA_growth(%)'] = df_res['EBITDA'].pct_change().multiply(100).round(2)

            # calculating EBITDA margin
            df_res['EBITDA_margin'] = (df_res['Sales'] / df_res['EBITDA']).round(2)

            return df_res

    # If 'Profit & Loss' section or table is not found, return None
    return f"Data not available for the symbol: {symb}"

df_res = p_n_l(symb)
# print(df_res)


# Specify the CSV file path
csv_file_path = 'profit_loss_data_' + symb + '.csv'

# Write the res DataFrame to a CSV file
df_res.to_csv(csv_file_path)

# Print a message indicating the CSV file has been created
# print(f'Res DataFrame has been written to {csv_file_path}')