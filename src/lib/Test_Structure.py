import filecmp
from pathlib import Path
import pandas as pd
# import unittest
# import file_unittest
# https://stackoverflow.com/questions/42512016/how-to-compare-two-files-as-part-of-unittest-while-getting-useful-output-in-cas

'''manually run and change the testing_xxx'''
testing_bulk  = Path.home() / 'AutoFeram' / 'output' / 'verification' / 'temperature_defaultseed_bulk_2024-10-15'   / 'thermo.avg'
testing_strnT = Path.home() / 'AutoFeram' / 'output' / 'verification' / 'temperature_defaultseed_strnT0.01_2024-10-15'  / 'thermo.avg'
testing_film  = Path.home() / 'AutoFeram' / 'output' / 'verification' / 'temperature_defaultseed_film_2024-10-15'   / 'thermo.avg'
testing_epit  = Path.home() / 'AutoFeram' / 'output' / 'verification' / 'temperature_defaultseed_epit_2024-10-15'  / 'thermo.avg'

'''do not touch the following'''
expected_bulk  = Path.home() / 'AutoFeram' / 'src' / 'lib' / 'test_expectedresults'  / 'structure' / 'temperature_defaultseed_bulk_2024-10-15'  / 'thermo.avg'
expected_strnT = Path.home() / 'AutoFeram' / 'src' / 'lib' / 'test_expectedresults'  / 'structure' / 'temperature_defaultseed_strnT0.01_2024-10-15' / 'thermo.avg'
expected_film  = Path.home() / 'AutoFeram' / 'src' / 'lib' / 'test_expectedresults'  / 'structure' / 'temperature_defaultseed_film_2024-10-15'  / 'thermo.avg'
expected_epit  = Path.home() / 'AutoFeram' / 'src' / 'lib' / 'test_expectedresults'  / 'structure' / 'temperature_defaultseed_epit_2024-10-15'  / 'thermo.avg'


if __name__ == '__main__':


    results = pd.DataFrame({'same':[
        (filecmp.cmp(expected_bulk, testing_bulk)),
        (filecmp.cmp(expected_strnT, testing_strnT)),
        (filecmp.cmp(expected_film, testing_film)),
        (filecmp.cmp(expected_epit, testing_epit)),
        ]}, index=['bulk', 'strnT', 'film', 'epit'])

#    print(results)
    if all(results['same']):
        print('clear. everything is fine.')
    else:
        print('The following are wrong:')
        mask = (results['same']==False)
        [ print(f'    {i}') for i in results[mask].index ]


