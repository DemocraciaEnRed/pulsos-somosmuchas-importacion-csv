from pandas import DataFrame, read_csv
import pandas as pd 
from sys import exit, argv
import re
from collections import namedtuple

def print_row_err(i, *args):
  print(f'ERR en línea {i+1}:', *args)
  
def sql_str(s):
  return '"{}"'.format(str(s).strip().replace('"', '\\"'))
  
social_media_regex = re.compile('.*\.com\/([\w@.-]+)')
email_regex = re.compile('[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}')
string_regex = re.compile("^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ '-]*$")
telefono_regex = re.compile('^[a-zA-Z0-9 +():.,/–-]*$')

file = argv[1]
df = pd.read_csv(file)
#nombres,apellidos,twitter (enlace),facebook (enlace),instagram (enlace),telefono,genero,cargo,departamento,partido,correo electrónico

# renombramos columnas para que sean accesibles con "."
df.rename(columns = {
  'twitter (enlace)': 'twitter',
  'facebook (enlace)': 'facebook',
  'instagram (enlace)': 'instagram',
  'correo electrónico': 'correo'
}, inplace=True)

# stripeamos
df.departamento = df.departamento.str.strip()
df.twitter = df.twitter.str.strip()
df.facebook = df.facebook.str.strip()
df.instagram = df.instagram.str.strip()
df.telefono = df.telefono.str.strip()

# neutralizamos género de senadorxs
df.cargo = df.cargo.replace('Senador de la República', 'Senador/a de la República').replace('Senadora de la República', 'Senador/a de la República')
  
def get_social_account(i, social_index):  
  if r[social_index] and not pd.isna(r[social_index]) and not r[social_index] == '-':
    match = social_media_regex.match(r[social_index])
    if not match:
      print_row_err(i, f'{social_index.title()} inválido {r[social_index]}')
    return match[1] or ''
  else:
    return ''

# generamos ids de cargo, dep. y parti.
# con el offset de 100 nos aseguramos que si había algo antes no choque
uniq_cargo = df.cargo.unique()
uniq_cargo.sort()
cargos = {}
for i, val in enumerate(uniq_cargo):
  cargos[val] = i+100
print(cargos)

uniq_departamento = df.departamento.unique()
uniq_departamento.sort()
departamentos = {}
for i, val in enumerate(uniq_departamento):
  departamentos[val] = i+100
print(departamentos)

uniq_partido = df.partido.unique()
uniq_partido.sort()
partidos = {}
for i, val in enumerate(uniq_partido):
  partidos[val] = i+100
print(partidos)
  
# main dataset de candidatxs
Politician = namedtuple('Politician', [
  'first_name',
	'last_name',
	'gender',
	'facebook',
	'twitter',
	'instagram',
	'phone',
	'position_id',
	'district_id',
	'party_id'
])
politicians = []

for i, r in df.iterrows():
  # chequear campos obligatorios
  if not r.nombres or pd.isna(r.nombres):
    print_row_err(i, 'Sin nombres')
    continue
  if not r.apellidos or pd.isna(r.apellidos):
    print_row_err(i, 'Sin apellidos')
    continue
  if not r.cargo or pd.isna(r.cargo):
    print_row_err(i, 'Sin cargo')
    continue
  if not r.departamento or pd.isna(r.departamento):
    print_row_err(i, 'Sin departamento')
    continue
  if not r.partido or pd.isna(r.partido):
    print_row_err(i, 'Sin partido')
    continue
    
  # chequear algunos campos con regex
  match = string_regex.match(r.nombres)
  if not match:
    print_row_err(i, f'Nombres inválido {r.nombres}')        
  match = string_regex.match(r.apellidos)
  if not match:
    print_row_err(i, f'Apellidos inválido {r.apellidos}')      
  if r.telefono and not pd.isna(r.telefono):
    match = telefono_regex.match(r.telefono)
    if not match:
      print_row_err(i, f'Teléfono inválido {r.telefono}')    
  if r.correo and not pd.isna(r.correo):
    match = email_regex.match(r.correo)
    if not match:
      print_row_err(i, f'Email inválido {r.correo}')    
    
  # género
  if r.genero not in ['F', 'M']:
    print_row_err(i, f'Genero inválido {r.genero}')    
    continue
  
  # cuentas sociales
  tw = get_social_account(i, 'twitter').replace('@', '')
  fb = get_social_account(i, 'facebook')
  ig = get_social_account(i, 'instagram')
  #print(f'{tw:<20} {fb:<28} {ig:<20}')
      
  politicians.append(Politician(
    sql_str(r.nombres),
    sql_str(r.apellidos),
    0 if r.genero == 'M' else 1,
    sql_str(fb),
    sql_str(tw),
    sql_str(ig),
    sql_str(r.telefono),
    cargos[r.cargo],
    departamentos[r.departamento],
    partidos[r.partido],
  ))
  #exit(0)

print(f'{len(politicians)} candidatxs procesadxs')


###########################################
###########################################
##### Comienzo de dump

sql_path = 'somosmuchas-importacion.sql'
sql_dump_file = open(sql_path, 'w+')
print(f'Dumpeando a {sql_path}')
def sql_dump_line(s): sql_dump_file.write(s + '\n')

# dumpeamos datos de tipos
for val, i in partidos.items():
  sql_dump_line(f'INSERT INTO parties (id, name) VALUES ({i}, "{val}");')

for val, i in departamentos.items():
  sql_dump_line(f'INSERT INTO districts (id, name) VALUES ({i}, "{val}");')

for val, i in cargos.items():
  sql_dump_line(f'INSERT INTO positions (id, name, modified) VALUES ({i}, "{val}", NOW());')
  
# dumpeamos candidatxs
sql_dump_line("INSERT INTO politicians (\
  first_name,\
	last_name,\
	gender,\
	facebook,\
	twitter,\
	instagram,\
	phone,\
	position_id,\
	district_id,\
	party_id,\
	created,\
	modified\
	) VALUES ".replace('\t','')
)

for i, p in enumerate(politicians):
  coma_vals = ', '.join([
    p.first_name,
    p.last_name,
    str(p.gender),
    p.facebook,
    p.twitter,
    p.instagram,
    p.phone,
    str(p.position_id),
    str(p.district_id),
    str(p.party_id),
    'NOW()',
    'NOW()'
  ])
  if i == len(politicians) - 1:
    sql_dump_line(f'({coma_vals});')
  else:
    sql_dump_line(f'({coma_vals}),')

# end
sql_dump_file.close()

print('Fin!')

exit(0)
