from datetime import datetime
from tqdm import tqdm
tqdm.pandas(desc="Progress")
start = datetime.now()
import pandas as pd
print(str(datetime.now()-start)+'\t Чтение файла...')
text_file = open("langs.txt", "r")
lines = text_file.readlines()
data = pd.DataFrame(lines)
data.columns=['text']

print(str(datetime.now()-start)+'\t Определение языка...')

from langdetect import detect
def ToStr(value):
    return detect(str(value))

data['lang'] = data['text'].progress_apply(ToStr)

print(str(datetime.now()-start)+'\t Результат:')
print(data['lang'].value_counts())

res = data['lang'].value_counts().tolist()


langs = [1 for x in res if x>10]
langcount=len(langs)

print('Количество языков:',langcount )
