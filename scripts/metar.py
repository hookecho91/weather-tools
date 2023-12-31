#!/Users/virgil/anaconda3/envs/metr/bin/python

import requests
from bs4 import BeautifulSoup
# import sys


def get_metar(icao, hoursback=120, format='json'):
    metar_url = f'https://aviationweather.gov/api/data/metar?ids={icao}&format={format}&hours={hoursback}'
    src = requests.get(metar_url).content
    return src


def metar_to_df(icao, **kwargs):
    global df
    icao = icao.upper()
    json_data = json.loads(get_metar(icao, **kwargs))
    for i,_ in enumerate(json_data):
        if i == 0:
            df = parse_metar_to_dataframe(
                json_data[i]['rawOb'], 
                month=pd.to_datetime(json_data[i]['receiptTime']).month, 
                year=pd.to_datetime(json_data[i]['receiptTime']).year
                )
        else:
            df = pd.concat(
                [
                    df, 
                    parse_metar_to_dataframe(
                        json_data[i]['rawOb'],
                        month=pd.to_datetime(json_data[i]['receiptTime']).month, 
                        year=pd.to_datetime(json_data[i]['receiptTime']).year
                    )
                ]
            )

    df['2m_temp'] = (df['air_temperature'] * 9/5) + 32
    df['2m_dew'] = (df['dew_point_temperature'] * 9/5) + 32
    df['2m_HI'] = to_heat_index(df['2m_temp'].values, df['2m_dew'].values)
    ## nan HI values where air temp < 80 F 
    df.loc[df['2m_temp'] < 80, ['2m_HI']] = np.nan
    df['2m_WC'] = to_wind_chill(df['2m_temp'].values, df['wind_speed'].values)
    ## nan wind chill values where speed <= 5 mph or air temp > 50
    df.loc[df['wind_speed'] <= 5, ['2m_WC']] = np.nan
    df.loc[df['2m_temp'] > 50, ['2m_WC']] = np.nan

    return df

if __name__ == '__main__':

    icao = input('Enter ICAO: ').upper()
    hoursback = input('Enter hours back (Leave blank for most recent): ')

    # if len(sys.argv) > 1:
    #     icao = str(sys.argv[1]).upper()
    # else:
    #     icao = 'KPIT'

    # if len(sys.argv) > 2:
    #     hoursback = sys.argv[2]
    # else:
    #     hoursback = None

    ob = get_metar(icao, hoursback)
    print(f'Latest observation(s) from {icao}:\n{ob}')
