import requests
from bs4 import BeautifulSoup
import sys
from metpy.io import parse_metar_to_dataframe
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import warnings


def get_metar_meteogram(icao, hoursback=None):
    """
    Download METAR from the NOAA Avation Weather Center

    Parameters
    ----------
    icao : str
        ICAO identifier used when reporting METARs
    hoursback : str or int
        Number of hours before present to query

    Returns
    ----------
    obs : str
        str with each observation as a seperate line (\n)
    """

    if hoursback:
        metar_url = f'https://www.aviationweather.gov/metar/data?ids={icao}&format=raw&date=&hours={hoursback}&taf=off'
    else:
        metar_url = f'https://www.aviationweather.gov/metar/data?ids={icao}&format=raw&date=&hours=0&taf=off'
    src = requests.get(metar_url).content
    soup = BeautifulSoup(src, "html.parser")
    metar_data = soup.find(id='awc_main_content_wrap')

    obs = ''
    for i in metar_data:
        if str(i).startswith('<code>'):
            line = str(i).lstrip('<code>').rstrip('</code>')
            obs+=line
            obs+='\n'
    return obs


def meteogram(icao, hoursback):
    """
    Create a simple meteogram from METARs and saves it as a .png file

    Parameters
    ----------
    icao : str
        ICAO identifier used when reporting METARs
    hoursback : str or int
        Number of hours before present to query

    Returns
    ----------
    fname : str
        location of saved meteogram .png file
    """

    # download METAR data with the provided ICAO as a string, then using Metpy, 
    # parse the string and add observations to a Pandas DataFrame
    # https://unidata.github.io/MetPy/latest/api/generated/metpy.io.parse_metar_to_dataframe.html#metpy.io.parse_metar_to_dataframe
    icaos = [icao.upper()]
    for i,icao in enumerate(icaos):
        txt = get_metar_meteogram(icao, hoursback).split('\n')[:-1]
        if i == 0:
            df = parse_metar_to_dataframe(txt[-1])
        for row in txt[::-1]:
            df = df.append(parse_metar_to_dataframe(row))

    WNDDIR = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']
    WNDDEG = np.arange(0, 361, 22.5)

    # create matplotlib figure to contain meteogram
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4,1,figsize=(12,15), dpi=200, sharex=True)
    fig.patch.set_facecolor('white')

    # first axis is temperature
    ax1.plot(df['date_time'], df['air_temperature'], label='$T$', linestyle='-', marker='', color='tab:red')
    ax1.plot(df['date_time'], df['dew_point_temperature'], label='$T_d$', linestyle='-', marker='', color='tab:green')
    ax1.set_ylabel('Temperature (degC)')
    ax1.set_xlabel('Z-Time (MM-DD HH)')
    ax1.set_title(f"{df['station_id'][0]}\n{df['date_time'][0].strftime('%Y-%m')}")
    # create custom xtick locations using pandas date range function
    ax1.set_xticks(pd.date_range(df['date_time'][0].strftime('%Y-%m-%d %H'), df['date_time'][-1].strftime('%Y-%m-%d %H'), freq='2H'))
    ax1.set_xticklabels(pd.date_range(df['date_time'][0].strftime('%Y-%m-%d %H'), df['date_time'][-1].strftime('%Y-%m-%d %H'), freq='2H').strftime('%m-%d %H%MZ'))
    ax1.grid(which='both')
    ax1.legend()

    # second axis is wind speed and direction
    ax2b = ax2.twinx()
    ax2.plot(df['date_time'], df['wind_speed'], label='Speed', linestyle='-', marker='', color='tab:blue')
    ax2b.plot(df['date_time'], df['wind_direction'], label='Direction', linestyle='', marker='*', color='tab:cyan')
    ax2.set_ylim([0, 40])
    ax2.set_ylabel('Wind Speed (kts)')
    ax2b.set_ylabel('Wind Direction (deg)')
    ax2b.set_ylim([-10,370])
    ax2b.set_yticks(WNDDEG[::2])
    ax2b.set_yticklabels(WNDDIR[::2])
    ax2.grid(which='both')

    # third axis is pressure
    ax3.plot(df['date_time'], df['altimeter'], label='Altimeter', linestyle='-', marker='', color='tab:brown')
    ax3.set_ylabel('Pressure (inHg)')
    ax3.grid(which='both')

    # fourth axis is cloud coverage reported
    
    # loop over each cloud level to plot. Use a list comprehension to ensure strings don't get passed to pyplot
    for etage in ['low', 'medium', 'high', 'highest']:
        cloud_heights = np.array([x if type(x) != str else np.nan for x in df[f'{etage}_cloud_level'].values])
        # plot clouds in units of thousands of feet (kft)
        ax4.plot(df['date_time'], cloud_heights/1000, label=etage, linestyle='', marker='*')

    ax4.set_ylim([0, 30])
    ax4.set_ylabel('Cloud Height (kft)')
    ax4.set_xlabel('Z-Time (MM-DD HH)')
    ax4.grid(which='both')
    ax4.legend()

    # format dates on x axis and save final meteogram
    fig.autofmt_xdate()
    fname = f"imgs/meteogram/metorgram_{df['station_id'][0]}.png"
    plt.savefig(fname, bbox_inches='tight')
    plt.close(fig)

    return fname


if __name__ == '__main__':
    # suppress warnings about NaNs
    warnings.simplefilter('ignore')

    # check to see if user provided a location
    if len(sys.argv) > 1:
        # save first command line argument following 'python' as the ICAO
        icao = str(sys.argv[1]).upper()
    else:
        # if no location provided, default to Pittsburgh
        icao = 'KPIT'

    # check to see if user provided a time frame
    if len(sys.argv) > 2:
        # save second command line argument as the hours back in time from present
        hoursback = sys.argv[2]
    else:
        # default hours back in time is one day (24 hours)
        hoursback = 24

    # call meteogram plotting function and print file path/name
    fname = meteogram(icao, hoursback)
    print(f'Meteogram for {icao} created.\n{fname}\n')
