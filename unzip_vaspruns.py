import zipfile
import os

os.makedirs('calc_80pct', exist_ok=True)
os.makedirs('calc_66pct', exist_ok=True)
os.makedirs('calc_90pct', exist_ok=True)
os.makedirs('results/sumo_dos', exist_ok=True)

with zipfile.ZipFile('vasprun.xml.zip', 'r') as z:
    z.extractall('calc_80pct/')
    print('Root:', z.namelist())

with zipfile.ZipFile('65_vasprun.xml.zip', 'r') as z:
    z.extractall('calc_66pct/')
    print('65_:', z.namelist())

with zipfile.ZipFile('90_vasprun.xml.zip', 'r') as z:
    z.extractall('calc_90pct/')
    print('90_:', z.namelist())

print('Done.')
